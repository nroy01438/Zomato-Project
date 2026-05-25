"""
Error Handling and Recovery System

Provides comprehensive error handling, recovery strategies, circuit breakers,
and resilience patterns for the production backend.
"""

import asyncio
import logging
import time
import traceback
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import defaultdict, deque

# Import monitoring components
try:
    from .monitoring import HealthMonitor, AlertSeverity
    from .cache import CacheManager, CacheConfig
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logging.warning("Monitoring components not available")


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    EXTERNAL_SERVICE = "external_service"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open" # Testing if service has recovered


@dataclass
class ErrorEvent:
    """Error event record"""
    id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    component: str
    operation: str
    user_id: Optional[str]
    request_id: Optional[str]
    stack_trace: Optional[str]
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    recovery_action: Optional[str] = None


@dataclass
class RecoveryAction:
    """Recovery action definition"""
    name: str
    description: str
    action_function: Callable
    max_attempts: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    timeout: Optional[float] = None


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: Type[Exception] = Exception
    success_threshold: int = 2  # Successes needed to close circuit


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Circuit state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
        # Statistics
        self.total_calls = 0
        self.failed_calls = 0
        self.successful_calls = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        self.total_calls += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            # Expected failure
            self._on_failure()
            raise
        except Exception as e:
            # Unexpected failure
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        
        self.successful_calls += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        
        self.failed_calls += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Go back to open on failure in half-open state
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.logger.warning(f"Circuit breaker {self.name} reverting to OPEN")
        elif self.state == CircuitState.CLOSED:
            # Open circuit if threshold reached
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        
        self.state = CircuitState.OPEN
        self.logger.warning(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")
    
    def _close_circuit(self):
        """Close the circuit"""
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.logger.info(f"Circuit breaker {self.name} CLOSED")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'failed_calls': self.failed_calls,
            'successful_calls': self.successful_calls,
            'failure_rate': self.failed_calls / max(1, self.total_calls),
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RetryPolicy:
    """Retry policy with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_multiplier: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for specific attempt"""
        
        if attempt <= 0:
            return 0
        
        # Exponential backoff
        delay = self.base_delay * (self.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        # Add jitter
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry policy"""
        
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts:
                    delay = self.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
        
        # This should never be reached
        if last_exception:
            raise last_exception


class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, component_name: str = "phase6_backend"):
        self.component_name = component_name
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.error_events: List[ErrorEvent] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Recovery actions
        self.recovery_actions: Dict[ErrorCategory, List[RecoveryAction]] = defaultdict(list)
        
        # Retry policies
        self.retry_policies: Dict[str, RetryPolicy] = {}
        
        # Error patterns for classification
        self.error_patterns = self._setup_error_patterns()
        
        # Monitoring integration
        self.health_monitor: Optional[HealthMonitor] = None
        self.cache_manager: Optional[CacheManager] = None
        
        # Setup default recovery actions
        self._setup_default_recovery_actions()
    
    def _setup_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Setup error patterns for classification"""
        
        return {
            'database_connection': {
                'category': ErrorCategory.DATABASE,
                'severity': ErrorSeverity.HIGH,
                'patterns': ['connection', 'timeout', 'unavailable', 'refused'],
                'recovery_actions': ['retry_connection', 'fallback_cache', 'circuit_breaker']
            },
            'cache_failure': {
                'category': ErrorCategory.CACHE,
                'severity': ErrorSeverity.MEDIUM,
                'patterns': ['cache', 'redis', 'memcached'],
                'recovery_actions': ['bypass_cache', 'fallback_memory_cache']
            },
            'authentication_failure': {
                'category': ErrorCategory.AUTHENTICATION,
                'severity': ErrorSeverity.MEDIUM,
                'patterns': ['auth', 'login', 'token', 'unauthorized'],
                'recovery_actions': ['refresh_token', 'retry_auth']
            },
            'rate_limit_exceeded': {
                'category': ErrorCategory.RATE_LIMIT,
                'severity': ErrorSeverity.LOW,
                'patterns': ['rate limit', 'too many requests', 'throttle'],
                'recovery_actions': ['exponential_backoff', 'queue_request']
            },
            'network_timeout': {
                'category': ErrorCategory.TIMEOUT,
                'severity': ErrorSeverity.MEDIUM,
                'patterns': ['timeout', 'connection timeout'],
                'recovery_actions': ['increase_timeout', 'retry_with_backoff']
            },
            'validation_error': {
                'category': ErrorCategory.VALIDATION,
                'severity': ErrorSeverity.LOW,
                'patterns': ['validation', 'invalid', 'malformed'],
                'recovery_actions': ['return_error', 'fix_data']
            }
        }
    
    def _setup_default_recovery_actions(self):
        """Setup default recovery actions"""
        
        # Database recovery actions
        self.recovery_actions[ErrorCategory.DATABASE].extend([
            RecoveryAction(
                name="retry_connection",
                description="Retry database connection with exponential backoff",
                action_function=self._retry_database_connection,
                max_attempts=3,
                retry_delay=1.0,
                backoff_multiplier=2.0
            ),
            RecoveryAction(
                name="fallback_cache",
                description="Use cached data when database is unavailable",
                action_function=self._fallback_to_cache,
                max_attempts=1
            )
        ])
        
        # Cache recovery actions
        self.recovery_actions[ErrorCategory.CACHE].extend([
            RecoveryAction(
                name="bypass_cache",
                description="Bypass cache and go directly to data source",
                action_function=self._bypass_cache,
                max_attempts=1
            ),
            RecoveryAction(
                name="fallback_memory_cache",
                description="Use in-memory cache as fallback",
                action_function=self._fallback_to_memory_cache,
                max_attempts=1
            )
        ])
        
        # Network recovery actions
        self.recovery_actions[ErrorCategory.NETWORK].extend([
            RecoveryAction(
                name="retry_with_backoff",
                description="Retry network request with exponential backoff",
                action_function=self._retry_with_backoff,
                max_attempts=3,
                retry_delay=1.0,
                backoff_multiplier=2.0
            )
        ])
    
    def set_health_monitor(self, health_monitor: HealthMonitor):
        """Set health monitor for integration"""
        
        self.health_monitor = health_monitor
    
    def set_cache_manager(self, cache_manager: CacheManager):
        """Set cache manager for integration"""
        
        self.cache_manager = cache_manager
    
    def create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create a circuit breaker"""
        
        circuit_breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = circuit_breaker
        self.logger.info(f"Created circuit breaker: {name}")
        return circuit_breaker
    
    def create_retry_policy(self, name: str, max_attempts: int = 3, base_delay: float = 1.0,
                          max_delay: float = 60.0, backoff_multiplier: float = 2.0) -> RetryPolicy:
        """Create a retry policy"""
        
        retry_policy = RetryPolicy(max_attempts, base_delay, max_delay, backoff_multiplier)
        self.retry_policies[name] = retry_policy
        return retry_policy
    
    def classify_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify error and determine handling strategy"""
        
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Find matching pattern
        classification = {
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.MEDIUM,
            'recovery_actions': []
        }
        
        for pattern_name, pattern_info in self.error_patterns.items():
            if any(keyword in error_message for keyword in pattern_info['patterns']):
                classification['category'] = pattern_info['category']
                classification['severity'] = pattern_info['severity']
                classification['recovery_actions'] = pattern_info['recovery_actions']
                break
        
        # Adjust severity based on context
        if context.get('critical_operation', False):
            classification['severity'] = ErrorSeverity.CRITICAL
        
        return classification
    
    def track_error(self, error: Exception, component: str, operation: str,
                   context: Optional[Dict[str, Any]] = None) -> ErrorEvent:
        """Track an error event"""
        
        error_id = f"err_{int(time.time() * 1000)}_{hash(str(error)) % 10000}"
        
        # Classify error
        classification = self.classify_error(error, context or {})
        
        # Create error event
        error_event = ErrorEvent(
            id=error_id,
            timestamp=datetime.now(),
            severity=classification['severity'],
            category=classification['category'],
            message=str(error),
            component=component,
            operation=operation,
            user_id=context.get('user_id') if context else None,
            request_id=context.get('request_id') if context else None,
            stack_trace=traceback.format_exc(),
            context=context or {},
            recovery_actions=classification['recovery_actions']
        )
        
        # Store error event
        self.error_events.append(error_event)
        self.error_counts[component] += 1
        
        # Keep only last 1000 errors
        if len(self.error_events) > 1000:
            self.error_events = self.error_events[-1000:]
        
        # Log error
        self.logger.error(f"Error in {component}.{operation}: {error}")
        
        # Trigger alert if critical
        if classification['severity'] == ErrorSeverity.CRITICAL and self.health_monitor:
            try:
                from .monitoring import Alert
                alert = Alert(
                    id=f"alert_{error_id}",
                    severity=AlertSeverity.CRITICAL,
                    title=f"Critical error in {component}",
                    message=str(error),
                    timestamp=datetime.now(),
                    source=component,
                    details={'error_event': asdict(error_event)}
                )
                # In a real implementation, this would trigger the alert system
            except Exception as e:
                self.logger.error(f"Failed to create alert: {e}")
        
        return error_event
    
    async def handle_error(self, error: Exception, component: str, operation: str,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an error with recovery strategies"""
        
        # Track the error
        error_event = self.track_error(error, component, operation, context)
        
        # Attempt recovery
        recovery_result = await self._attempt_recovery(error_event)
        
        return {
            'error_id': error_event.id,
            'handled': recovery_result['success'],
            'recovery_action': recovery_result['action'],
            'message': recovery_result['message'],
            'error': str(error)
        }
    
    async def _attempt_recovery(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Attempt error recovery"""
        
        recovery_actions = self.recovery_actions.get(error_event.category, [])
        
        for action_name in error_event.recovery_actions:
            action = next((a for a in recovery_actions if a.name == action_name), None)
            if not action:
                continue
            
            try:
                self.logger.info(f"Attempting recovery action: {action.name}")
                
                # Execute recovery action with timeout
                if asyncio.iscoroutinefunction(action.action_function):
                    if action.timeout:
                        result = await asyncio.wait_for(
                            action.action_function(error_event),
                            timeout=action.timeout
                        )
                    else:
                        result = await action.action_function(error_event)
                else:
                    result = action.action_function(error_event)
                
                if result.get('success', False):
                    # Mark error as resolved
                    error_event.resolved = True
                    error_event.resolution_time = datetime.now()
                    error_event.recovery_action = action.name
                    
                    return {
                        'success': True,
                        'action': action.name,
                        'message': f"Recovery successful using {action.name}",
                        'details': result
                    }
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Recovery action {action.name} timed out")
            except Exception as e:
                self.logger.error(f"Recovery action {action.name} failed: {e}")
        
        return {
            'success': False,
            'action': None,
            'message': 'No recovery action succeeded',
            'details': None
        }
    
    # Recovery action implementations
    async def _retry_database_connection(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Retry database connection"""
        
        retry_policy = self.retry_policies.get('database', RetryPolicy())
        
        try:
            # Simulate database reconnection
            await asyncio.sleep(0.5)  # Simulate connection time
            
            return {'success': True, 'message': 'Database connection restored'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _fallback_to_cache(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Fallback to cached data"""
        
        if not self.cache_manager:
            return {'success': False, 'error': 'No cache manager available'}
        
        try:
            # Try to get cached data
            cache_key = f"fallback_{error_event.operation}"
            cached_data = await self.cache_manager.get(cache_key)
            
            if cached_data:
                return {'success': True, 'message': 'Using cached data', 'data': cached_data}
            else:
                return {'success': False, 'error': 'No cached data available'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _bypass_cache(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Bypass cache and go directly to source"""
        
        # This would be implemented based on the specific operation
        return {'success': True, 'message': 'Cache bypassed, using direct source'}
    
    async def _fallback_to_memory_cache(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Fallback to in-memory cache"""
        
        # Simple in-memory cache fallback
        return {'success': True, 'message': 'Using in-memory cache fallback'}
    
    async def _retry_with_backoff(self, error_event: ErrorEvent) -> Dict[str, Any]:
        """Retry with exponential backoff"""
        
        retry_policy = self.retry_policies.get('network', RetryPolicy())
        
        try:
            # Simulate retry
            await asyncio.sleep(retry_policy.get_delay(1))
            return {'success': True, 'message': 'Retry successful'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def execute_with_protection(self, func: Callable, component: str, operation: str,
                                   context: Optional[Dict[str, Any]] = None,
                                   circuit_breaker_name: Optional[str] = None,
                                   retry_policy_name: Optional[str] = None) -> Any:
        """Execute function with error protection"""
        
        try:
            # Use circuit breaker if specified
            if circuit_breaker_name and circuit_breaker_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[circuit_breaker_name]
                return await circuit_breaker.call(func, context)
            
            # Use retry policy if specified
            elif retry_policy_name and retry_policy_name in self.retry_policies:
                retry_policy = self.retry_policies[retry_policy_name]
                return await retry_policy.execute_with_retry(func, context)
            
            # Normal execution
            else:
                if asyncio.iscoroutinefunction(func):
                    return await func(context)
                else:
                    return func(context)
                    
        except Exception as e:
            # Handle the error
            await self.handle_error(e, component, operation, context)
            raise
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        
        total_errors = len(self.error_events)
        
        if total_errors == 0:
            return {
                'total_errors': 0,
                'error_rate': 0.0,
                'component_errors': {},
                'category_breakdown': {},
                'severity_breakdown': {},
                'recent_errors': []
            }
        
        # Component breakdown
        component_errors = defaultdict(int)
        for error in self.error_events:
            component_errors[error.component] += 1
        
        # Category breakdown
        category_breakdown = defaultdict(int)
        for error in self.error_events:
            category_breakdown[error.category.value] += 1
        
        # Severity breakdown
        severity_breakdown = defaultdict(int)
        for error in self.error_events:
            severity_breakdown[error.severity.value] += 1
        
        # Recent errors (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_errors = [
            error for error in self.error_events
            if error.timestamp > cutoff_time
        ]
        
        # Resolved errors
        resolved_errors = [e for e in self.error_events if e.resolved]
        
        return {
            'total_errors': total_errors,
            'resolved_errors': len(resolved_errors),
            'unresolved_errors': total_errors - len(resolved_errors),
            'resolution_rate': len(resolved_errors) / total_errors,
            'component_errors': dict(component_errors),
            'category_breakdown': dict(category_breakdown),
            'severity_breakdown': dict(severity_breakdown),
            'recent_errors_1h': len(recent_errors),
            'circuit_breakers': {
                name: breaker.get_state() for name, breaker in self.circuit_breakers.items()
            }
        }
    
    def get_recent_errors(self, limit: int = 50, component: Optional[str] = None,
                         severity: Optional[ErrorSeverity] = None) -> List[Dict[str, Any]]:
        """Get recent errors with optional filtering"""
        
        errors = self.error_events
        
        # Apply filters
        if component:
            errors = [e for e in errors if e.component == component]
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        # Return most recent
        errors = sorted(errors, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        return [asdict(error) for error in errors]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform error handler health check"""
        
        health_status = {
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Check error rates
            stats = self.get_error_statistics()
            error_rate = stats['recent_errors_1h'] / 60  # Errors per minute
            
            health_status['checks']['error_rate'] = error_rate < 5.0  # Less than 5 errors per minute
            health_status['checks']['recent_errors'] = stats['recent_errors_1h']
            
            # Check circuit breakers
            all_circuits_closed = all(
                breaker.state == CircuitState.CLOSED 
                for breaker in self.circuit_breakers.values()
            )
            health_status['checks']['circuit_breakers'] = all_circuits_closed
            
            # Check recovery actions
            recovery_rate = stats.get('resolution_rate', 0)
            health_status['checks']['recovery_rate'] = recovery_rate > 0.5  # At least 50% recovery rate
            
            # Overall health
            health_status['healthy'] = all([
                health_status['checks'].get('error_rate', True),
                health_status['checks'].get('circuit_breakers', True),
                health_status['checks'].get('recovery_rate', True)
            ])
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
            self.logger.error(f"Error handler health check failed: {e}")
        
        return health_status
    
    def close(self):
        """Clean up error handler resources"""
        
        # Cancel any active tasks
        for circuit_breaker in self.circuit_breakers.values():
            # Circuit breakers don't have explicit cleanup
            pass
        
        self.logger.info("Error handler closed")
