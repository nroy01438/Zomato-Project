"""
Rate Limiting and Throttling System

Provides advanced rate limiting with multiple algorithms, distributed support,
user-based limits, and intelligent throttling for production backend.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import defaultdict, deque

# Import cache manager for distributed rate limiting
try:
    from .cache import CacheManager, CacheConfig
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logging.warning("Cache manager not available, using in-memory rate limiting")


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_window: int = 100
    window_seconds: int = 60
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    burst_size: Optional[int] = None
    distributed: bool = False
    key_prefix: str = "rate_limit:"


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining_requests: int
    reset_time: datetime
    retry_after: Optional[int] = None
    current_usage: int = 0
    limit: int = 0


@dataclass
class RateLimitMetrics:
    """Rate limiting metrics"""
    total_requests: int = 0
    blocked_requests: int = 0
    allowed_requests: int = 0
    average_response_time_ms: float = 0.0
    peak_requests_per_minute: int = 0


class TokenBucket:
    """Token bucket algorithm implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from bucket"""
        
        with self.lock:
            now = time.time()
            
            # Refill tokens
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Check if enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_tokens(self) -> float:
        """Get current token count"""
        
        with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            return min(self.capacity, self.tokens + tokens_to_add)


class SlidingWindow:
    """Sliding window algorithm implementation"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # in seconds
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = threading.Lock()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed"""
        
        with self.lock:
            now = time.time()
            cutoff_time = now - self.window_size
            
            # Remove old requests
            while self.requests and self.requests[0] <= cutoff_time:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, self.max_requests - len(self.requests)
            
            return False, 0
    
    def get_current_usage(self) -> int:
        """Get current request count"""
        
        with self.lock:
            now = time.time()
            cutoff_time = now - self.window_size
            
            # Remove old requests
            while self.requests and self.requests[0] <= cutoff_time:
                self.requests.popleft()
            
            return len(self.requests)


class FixedWindow:
    """Fixed window algorithm implementation"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # in seconds
        self.max_requests = max_requests
        self.current_window_start = int(time.time() // window_size)
        self.request_count = 0
        self.lock = threading.Lock()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed"""
        
        with self.lock:
            now = time.time()
            current_window = int(now // self.window_size)
            
            # Reset if new window
            if current_window != self.current_window_start:
                self.current_window_start = current_window
                self.request_count = 0
            
            # Check if under limit
            if self.request_count < self.max_requests:
                self.request_count += 1
                remaining = self.max_requests - self.request_count
                return True, remaining
            
            return False, 0
    
    def get_current_usage(self) -> int:
        """Get current request count"""
        
        with self.lock:
            now = time.time()
            current_window = int(now // self.window_size)
            
            if current_window != self.current_window_start:
                return 0
            
            return self.request_count


class LeakyBucket:
    """Leaky bucket algorithm implementation"""
    
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.queue = deque()
        self.last_leak = time.time()
        self.lock = threading.Lock()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed"""
        
        with self.lock:
            now = time.time()
            
            # Leak requests
            time_passed = now - self.last_leak
            requests_to_leak = int(time_passed * self.leak_rate)
            
            for _ in range(min(requests_to_leak, len(self.queue))):
                self.queue.popleft()
            
            self.last_leak = now
            
            # Check if queue has space
            if len(self.queue) < self.capacity:
                self.queue.append(now)
                remaining = self.capacity - len(self.queue)
                return True, remaining
            
            return False, 0
    
    def get_current_usage(self) -> int:
        """Get current queue size"""
        
        with self.lock:
            now = time.time()
            time_passed = now - self.last_leak
            requests_to_leak = int(time_passed * self.leak_rate)
            
            current_size = max(0, len(self.queue) - requests_to_leak)
            return current_size


class RateLimiter:
    """Production-ready rate limiter with multiple algorithms"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # In-memory limiters for non-distributed mode
        self.limiters: Dict[str, Any] = {}
        
        # Metrics
        self.metrics = RateLimitMetrics()
        self.peak_tracking: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))  # Last 60 seconds
        
        # Default configurations
        self.default_configs = {
            'global': RateLimitConfig(1000, 60, RateLimitAlgorithm.TOKEN_BUCKET),
            'per_user': RateLimitConfig(100, 60, RateLimitAlgorithm.SLIDING_WINDOW),
            'per_ip': RateLimitConfig(200, 60, RateLimitAlgorithm.SLIDING_WINDOW),
            'auth': RateLimitConfig(10, 60, RateLimitAlgorithm.SLIDING_WINDOW),
            'recommendations': RateLimitConfig(50, 60, RateLimitAlgorithm.TOKEN_BUCKET),
            'batch': RateLimitConfig(5, 60, RateLimitAlgorithm.FIXED_WINDOW)
        }
    
    def _get_limiter(self, key: str, config: RateLimitConfig) -> Any:
        """Get or create limiter for specific key"""
        
        if key not in self.limiters:
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                burst_size = config.burst_size or config.requests_per_window
                refill_rate = config.requests_per_window / config.window_seconds
                self.limiters[key] = TokenBucket(burst_size, refill_rate)
                
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                self.limiters[key] = SlidingWindow(config.window_seconds, config.requests_per_window)
                
            elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                self.limiters[key] = FixedWindow(config.window_seconds, config.requests_per_window)
                
            elif config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                leak_rate = config.requests_per_window / config.window_seconds
                self.limiters[key] = LeakyBucket(config.requests_per_window, leak_rate)
        
        return self.limiters[key]
    
    async def check_rate_limit(self, key: str, config: Optional[RateLimitConfig] = None,
                              identifier: Optional[str] = None) -> RateLimitResult:
        """Check if request is allowed under rate limit"""
        
        start_time = time.time()
        
        # Use default config if not provided
        if config is None:
            config = self.default_configs.get(key, self.default_configs['global'])
        
        # Create full key
        full_key = f"{config.key_prefix}{key}"
        if identifier:
            full_key += f":{identifier}"
        
        # Update metrics
        self.metrics.total_requests += 1
        
        try:
            if config.distributed and self.cache_manager:
                # Distributed rate limiting using cache
                result = await self._check_distributed_rate_limit(full_key, config)
            else:
                # In-memory rate limiting
                result = await self._check_memory_rate_limit(full_key, config)
            
            # Update peak tracking
            self._update_peak_tracking(key)
            
            # Update metrics
            if result.allowed:
                self.metrics.allowed_requests += 1
            else:
                self.metrics.blocked_requests += 1
            
            # Update average response time
            response_time = (time.time() - start_time) * 1000
            total_requests = self.metrics.allowed_requests + self.metrics.blocked_requests
            if total_requests > 0:
                self.metrics.average_response_time_ms = (
                    (self.metrics.average_response_time_ms * (total_requests - 1) + response_time) / total_requests
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if rate limiting fails
            return RateLimitResult(
                allowed=True,
                remaining_requests=config.requests_per_window,
                reset_time=datetime.now() + timedelta(seconds=config.window_seconds)
            )
    
    async def _check_memory_rate_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using in-memory algorithm"""
        
        limiter = self._get_limiter(key, config)
        
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            allowed = limiter.consume()
            remaining = int(limiter.get_tokens())
            
        elif config.algorithm in [RateLimitAlgorithm.SLIDING_WINDOW, RateLimitAlgorithm.FIXED_WINDOW, RateLimitAlgorithm.LEAKY_BUCKET]:
            allowed, remaining = limiter.is_allowed()
        else:
            allowed = True
            remaining = config.requests_per_window
        
        # Calculate reset time
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            # Token bucket resets based on refill rate
            tokens_needed = config.requests_per_window - remaining
            reset_time = datetime.now() + timedelta(seconds=tokens_needed / (config.requests_per_window / config.window_seconds))
        else:
            # Other algorithms reset at window boundary
            reset_time = datetime.now() + timedelta(seconds=config.window_seconds)
        
        current_usage = config.requests_per_window - remaining
        
        return RateLimitResult(
            allowed=allowed,
            remaining_requests=remaining,
            reset_time=reset_time,
            retry_after=None if allowed else int(config.window_seconds),
            current_usage=current_usage,
            limit=config.requests_per_window
        )
    
    async def _check_distributed_rate_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using distributed cache"""
        
        if not self.cache_manager:
            # Fallback to memory rate limiting
            return await self._check_memory_rate_limit(key, config)
        
        # Use sliding window for distributed rate limiting
        now = int(time.time())
        window_start = now - config.window_seconds
        
        # Get current requests in window
        cache_key = f"{key}:requests"
        cached_requests = await self.cache_manager.get(cache_key)
        
        if cached_requests is None:
            cached_requests = []
        else:
            # Filter out old requests
            cached_requests = [req_time for req_time in cached_requests if req_time > window_start]
        
        # Check if under limit
        if len(cached_requests) < config.requests_per_window:
            # Add current request
            cached_requests.append(now)
            await self.cache_manager.set(cache_key, cached_requests, config.window_seconds)
            
            return RateLimitResult(
                allowed=True,
                remaining_requests=config.requests_per_window - len(cached_requests),
                reset_time=datetime.now() + timedelta(seconds=config.window_seconds),
                current_usage=len(cached_requests),
                limit=config.requests_per_window
            )
        else:
            # Rate limited
            oldest_request = min(cached_requests)
            retry_after = int(oldest_request + config.window_seconds - now)
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=datetime.fromtimestamp(oldest_request + config.window_seconds),
                retry_after=max(1, retry_after),
                current_usage=len(cached_requests),
                limit=config.requests_per_window
            )
    
    def _update_peak_tracking(self, key: str):
        """Update peak request tracking"""
        
        now = int(time.time())
        self.peak_tracking[key].append(now)
        
        # Update peak requests per minute
        requests_in_last_minute = len(self.peak_tracking[key])
        if requests_in_last_minute > self.metrics.peak_requests_per_minute:
            self.metrics.peak_requests_per_minute = requests_in_last_minute
    
    async def check_multiple_limits(self, checks: List[Tuple[str, Optional[str]]]) -> RateLimitResult:
        """Check multiple rate limits and return the most restrictive"""
        
        results = []
        
        for limit_key, identifier in checks:
            config = self.default_configs.get(limit_key, self.default_configs['global'])
            result = await self.check_rate_limit(limit_key, config, identifier)
            results.append(result)
        
        # Find most restrictive result
        if not results:
            return RateLimitResult(
                allowed=True,
                remaining_requests=1000,
                reset_time=datetime.now() + timedelta(seconds=60)
            )
        
        # If any limit is exceeded, return the first blocked result
        blocked_result = next((r for r in results if not r.allowed), None)
        if blocked_result:
            return blocked_result
        
        # Otherwise, return the result with minimum remaining requests
        most_restrictive = min(results, key=lambda r: r.remaining_requests)
        return most_restrictive
    
    # Predefined rate limit checks
    async def check_global_limit(self) -> RateLimitResult:
        """Check global rate limit"""
        return await self.check_rate_limit('global')
    
    async def check_user_limit(self, user_id: str) -> RateLimitResult:
        """Check per-user rate limit"""
        return await self.check_rate_limit('per_user', identifier=user_id)
    
    async def check_ip_limit(self, ip_address: str) -> RateLimitResult:
        """Check per-IP rate limit"""
        return await self.check_rate_limit('per_ip', identifier=ip_address)
    
    async def check_auth_limit(self, identifier: str) -> RateLimitResult:
        """Check authentication rate limit"""
        return await self.check_rate_limit('auth', identifier=identifier)
    
    async def check_recommendation_limit(self, user_id: Optional[str] = None) -> RateLimitResult:
        """Check recommendation rate limit"""
        return await self.check_rate_limit('recommendations', identifier=user_id)
    
    async def check_batch_limit(self, user_id: Optional[str] = None) -> RateLimitResult:
        """Check batch operation rate limit"""
        return await self.check_rate_limit('batch', identifier=user_id)
    
    # Configuration management
    def set_rate_limit_config(self, key: str, config: RateLimitConfig):
        """Set rate limit configuration for a specific key"""
        self.default_configs[key] = config
        self.logger.info(f"Rate limit config updated for {key}")
    
    def get_rate_limit_config(self, key: str) -> Optional[RateLimitConfig]:
        """Get rate limit configuration for a specific key"""
        return self.default_configs.get(key)
    
    # Metrics and monitoring
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        
        return {
            'total_requests': self.metrics.total_requests,
            'blocked_requests': self.metrics.blocked_requests,
            'allowed_requests': self.metrics.allowed_requests,
            'block_rate': self.metrics.blocked_requests / max(1, self.metrics.total_requests),
            'average_response_time_ms': self.metrics.average_response_time_ms,
            'peak_requests_per_minute': self.metrics.peak_requests_per_minute,
            'active_limiters': len(self.limiters),
            'distributed_mode': self.cache_manager is not None
        }
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed rate limiting statistics"""
        
        stats = self.get_metrics()
        
        # Add per-key statistics
        per_key_stats = {}
        for key, config in self.default_configs.items():
            per_key_stats[key] = {
                'requests_per_window': config.requests_per_window,
                'window_seconds': config.window_seconds,
                'algorithm': config.algorithm.value,
                'distributed': config.distributed
            }
        
        stats['per_key_configurations'] = per_key_stats
        
        # Add current usage for each key
        current_usage = {}
        for key in self.limiters.keys():
            limiter = self.limiters[key]
            if hasattr(limiter, 'get_current_usage'):
                current_usage[key] = limiter.get_current_usage()
            elif hasattr(limiter, 'get_tokens'):
                current_usage[key] = int(limiter.get_tokens())
        
        stats['current_usage'] = current_usage
        
        return stats
    
    async def reset_rate_limits(self, key_pattern: Optional[str] = None):
        """Reset rate limits"""
        
        if key_pattern:
            # Reset specific limiters
            keys_to_reset = [k for k in self.limiters.keys() if key_pattern in k]
            for key in keys_to_reset:
                del self.limiters[key]
            
            # Clear cache entries if distributed
            if self.cache_manager:
                await self.cache_manager.clear(f"{key_pattern}*")
            
            self.logger.info(f"Reset rate limits matching pattern: {key_pattern}")
        else:
            # Reset all limiters
            self.limiters.clear()
            
            # Clear all rate limit cache entries
            if self.cache_manager:
                await self.cache_manager.clear("rate_limit:*")
            
            self.logger.info("Reset all rate limits")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform rate limiter health check"""
        
        health_status = {
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Test rate limiting functionality
            test_key = f"health_check_{int(time.time())}"
            test_config = RateLimitConfig(5, 10, RateLimitAlgorithm.TOKEN_BUCKET)
            
            # Should allow first request
            result1 = await self.check_rate_limit(test_key, test_config)
            health_status['checks']['first_request_allowed'] = result1.allowed
            
            # Should allow subsequent requests up to limit
            allowed_count = 0
            for i in range(5):
                result = await self.check_rate_limit(test_key, test_config)
                if result.allowed:
                    allowed_count += 1
            
            health_status['checks']['requests_within_limit'] = allowed_count == 5
            
            # Should block requests beyond limit
            result_blocked = await self.check_rate_limit(test_key, test_config)
            health_status['checks']['request_blocked'] = not result_blocked.allowed
            
            # Test distributed mode if available
            if self.cache_manager:
                cache_health = await self.cache_manager.health_check()
                health_status['checks']['cache_healthy'] = cache_health['healthy']
            
            # Overall health
            health_status['healthy'] = all(
                health_status['checks'].get(check, True) 
                for check in ['first_request_allowed', 'requests_within_limit', 'request_blocked']
            )
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
            self.logger.error(f"Rate limiter health check failed: {e}")
        
        return health_status
    
    def close(self):
        """Clean up rate limiter resources"""
        
        self.limiters.clear()
        self.peak_tracking.clear()
        
        if self.cache_manager:
            self.cache_manager.close()
        
        self.logger.info("Rate limiter closed")


# Rate limiting middleware for API Gateway
class RateLimitMiddleware:
    """Rate limiting middleware for API Gateway"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)
    
    async def check_request_limits(self, request_context: Dict[str, Any]) -> RateLimitResult:
        """Check all applicable rate limits for a request"""
        
        checks = []
        
        # Always check global limit
        checks.append(('global', None))
        
        # Check IP-based limit
        ip_address = request_context.get('ip_address')
        if ip_address:
            checks.append(('per_ip', ip_address))
        
        # Check user-based limit
        user_id = request_context.get('user_id')
        if user_id:
            checks.append(('per_user', user_id))
        
        # Check endpoint-specific limits
        path = request_context.get('path', '')
        if '/recommend' in path:
            checks.append(('recommendations', user_id))
        elif '/auth/login' in path:
            checks.append(('auth', ip_address))
        elif '/batch' in path:
            checks.append(('batch', user_id))
        
        return await self.rate_limiter.check_multiple_limits(checks)
    
    def create_rate_limit_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Create rate limit response headers"""
        
        headers = {}
        
        if result.allowed:
            headers['X-RateLimit-Limit'] = str(result.limit)
            headers['X-RateLimit-Remaining'] = str(result.remaining_requests)
            headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
        else:
            headers['X-RateLimit-Limit'] = str(result.limit)
            headers['X-RateLimit-Remaining'] = '0'
            headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
            
            if result.retry_after:
                headers['Retry-After'] = str(result.retry_after)
        
        return headers
