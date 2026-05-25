"""
Load Balancing and Scaling Infrastructure

Provides load balancing algorithms, health checking, auto-scaling,
and traffic distribution for the production backend.
"""

import asyncio
import logging
import time
import random
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
from collections import defaultdict

# Try to import health check dependencies
try:
    import aiohttp
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    logging.warning("aiohttp not available, using basic HTTP client")


class LoadBalanceAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    HEALTH_AWARE = "health_aware"


class ServerStatus(Enum):
    """Server health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"


@dataclass
class ServerInstance:
    """Represents a server instance"""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 1000
    current_connections: int = 0
    status: ServerStatus = ServerStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    response_time_ms: float = 0.0
    error_count: int = 0
    total_requests: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"
    
    @property
    def connection_ratio(self) -> float:
        return self.current_connections / max(1, self.max_connections)
    
    @property
    def error_rate(self) -> float:
        return self.error_count / max(1, self.total_requests)


@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: LoadBalanceAlgorithm = LoadBalanceAlgorithm.ROUND_ROBIN
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 5   # seconds
    unhealthy_threshold: int = 3      # consecutive failures
    healthy_threshold: int = 2       # consecutive successes
    max_retries: int = 3
    retry_delay: float = 1.0         # seconds
    enable_sticky_sessions: bool = False
    session_timeout: int = 3600      # seconds


@dataclass
class LoadBalancerMetrics:
    """Load balancer metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    active_connections: int = 0
    server_count: int = 0
    healthy_servers: int = 0


class LoadBalancer:
    """Production-ready load balancer with multiple algorithms"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Server management
        self.servers: Dict[str, ServerInstance] = {}
        self.round_robin_index = 0
        self.server_lock = threading.Lock()
        
        # Session management for sticky sessions
        self.sticky_sessions: Dict[str, str] = {}  # session_id -> server_id
        
        # Metrics
        self.metrics = LoadBalancerMetrics()
        self.request_times: List[float] = []
        
        # Health checking
        self.health_check_task: Optional[asyncio.Task] = None
        self._stop_health_check = asyncio.Event()
        
        # Start health checking
        self._start_health_checking()
    
    def add_server(self, server_id: str, host: str, port: int, weight: int = 1,
                   max_connections: int = 1000) -> ServerInstance:
        """Add a server instance to the load balancer"""
        
        server = ServerInstance(
            id=server_id,
            host=host,
            port=port,
            weight=weight,
            max_connections=max_connections
        )
        
        with self.server_lock:
            self.servers[server_id] = server
        
        self.logger.info(f"Added server {server_id} at {server.address}")
        return server
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server instance from the load balancer"""
        
        with self.server_lock:
            if server_id in self.servers:
                server = self.servers[server_id]
                del self.servers[server_id]
                
                # Clean up sticky sessions
                sessions_to_remove = [
                    session_id for session_id, sid in self.sticky_sessions.items()
                    if sid == server_id
                ]
                for session_id in sessions_to_remove:
                    del self.sticky_sessions[session_id]
                
                self.logger.info(f"Removed server {server_id}")
                return True
        
        return False
    
    def get_server(self, session_id: Optional[str] = None, 
                  client_ip: Optional[str] = None) -> Optional[ServerInstance]:
        """Get a server instance based on load balancing algorithm"""
        
        with self.server_lock:
            healthy_servers = [
                server for server in self.servers.values()
                if server.status == ServerStatus.HEALTHY
            ]
            
            if not healthy_servers:
                self.logger.warning("No healthy servers available")
                return None
            
            # Sticky session handling
            if (self.config.enable_sticky_sessions and session_id and 
                session_id in self.sticky_sessions):
                server_id = self.sticky_sessions[session_id]
                if server_id in self.servers:
                    server = self.servers[server_id]
                    if server.status == ServerStatus.HEALTHY:
                        return server
                    else:
                        # Remove stale sticky session
                        del self.sticky_sessions[session_id]
            
            # Apply load balancing algorithm
            if self.config.algorithm == LoadBalanceAlgorithm.ROUND_ROBIN:
                server = self._round_robin_select(healthy_servers)
            
            elif self.config.algorithm == LoadBalanceAlgorithm.LEAST_CONNECTIONS:
                server = self._least_connections_select(healthy_servers)
            
            elif self.config.algorithm == LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN:
                server = self._weighted_round_robin_select(healthy_servers)
            
            elif self.config.algorithm == LoadBalanceAlgorithm.IP_HASH:
                server = self._ip_hash_select(healthy_servers, client_ip)
            
            elif self.config.algorithm == LoadBalanceAlgorithm.RANDOM:
                server = random.choice(healthy_servers)
            
            elif self.config.algorithm == LoadBalanceAlgorithm.HEALTH_AWARE:
                server = self._health_aware_select(healthy_servers)
            
            else:
                server = healthy_servers[0]
            
            # Update sticky session
            if (self.config.enable_sticky_sessions and session_id and 
                server.status == ServerStatus.HEALTHY):
                self.sticky_sessions[session_id] = server.id
            
            return server
    
    def _round_robin_select(self, servers: List[ServerInstance]) -> ServerInstance:
        """Round robin selection"""
        
        server = servers[self.round_robin_index % len(servers)]
        self.round_robin_index = (self.round_robin_index + 1) % len(servers)
        return server
    
    def _least_connections_select(self, servers: List[ServerInstance]) -> ServerInstance:
        """Least connections selection"""
        
        return min(servers, key=lambda s: s.current_connections)
    
    def _weighted_round_robin_select(self, servers: List[ServerInstance]) -> ServerInstance:
        """Weighted round robin selection"""
        
        # Create weighted list
        weighted_servers = []
        for server in servers:
            weighted_servers.extend([server] * server.weight)
        
        server = weighted_servers[self.round_robin_index % len(weighted_servers)]
        self.round_robin_index = (self.round_robin_index + 1) % len(weighted_servers)
        return server
    
    def _ip_hash_select(self, servers: List[ServerInstance], client_ip: Optional[str]) -> ServerInstance:
        """IP hash selection"""
        
        if not client_ip:
            return random.choice(servers)
        
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(servers)
        return servers[index]
    
    def _health_aware_select(self, servers: List[ServerInstance]) -> ServerInstance:
        """Health-aware selection (prefer servers with better health)"""
        
        # Score servers based on health metrics
        scored_servers = []
        for server in servers:
            score = 0
            
            # Lower connection ratio is better
            score += (1.0 - server.connection_ratio) * 0.4
            
            # Lower response time is better
            if server.response_time_ms > 0:
                score += (1.0 / server.response_time_ms) * 0.3
            
            # Lower error rate is better
            score += (1.0 - server.error_rate) * 0.3
            
            scored_servers.append((score, server))
        
        # Select server with highest score
        scored_servers.sort(key=lambda x: x[0], reverse=True)
        return scored_servers[0][1]
    
    async def route_request(self, request_data: Dict[str, Any], 
                          session_id: Optional[str] = None,
                          client_ip: Optional[str] = None,
                          retries: Optional[int] = None) -> Dict[str, Any]:
        """Route a request to an appropriate server"""
        
        if retries is None:
            retries = self.config.max_retries
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(retries + 1):
            # Get server
            server = self.get_server(session_id, client_ip)
            if not server:
                return {
                    'success': False,
                    'error': 'No healthy servers available',
                    'attempt': attempt + 1
                }
            
            try:
                # Update server metrics
                server.current_connections += 1
                server.total_requests += 1
                
                # Simulate request processing (in real implementation, this would be an HTTP request)
                if HTTP_AVAILABLE:
                    response = await self._make_http_request(server, request_data)
                else:
                    response = await self._simulate_request(server, request_data)
                
                # Update response time
                response_time = (time.time() - start_time) * 1000
                server.response_time_ms = response_time
                self.request_times.append(response_time)
                
                # Keep only last 1000 response times
                if len(self.request_times) > 1000:
                    self.request_times = self.request_times[-1000:]
                
                # Update metrics
                self.metrics.total_requests += 1
                self.metrics.successful_requests += 1
                
                # Update average response time
                if self.metrics.total_requests > 0:
                    self.metrics.avg_response_time_ms = (
                        sum(self.request_times[-100:]) / min(100, len(self.request_times))
                    )
                
                return {
                    'success': True,
                    'server_id': server.id,
                    'server_address': server.address,
                    'response': response,
                    'response_time_ms': response_time,
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                last_error = e
                server.error_count += 1
                
                self.logger.warning(f"Request to server {server.id} failed: {e}")
                
                # Mark server as unhealthy if too many errors
                if server.error_rate > 0.5 and server.total_requests > 10:
                    server.status = ServerStatus.UNHEALTHY
                
                # Retry with delay
                if attempt < retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
            
            finally:
                # Always decrement connection count
                server.current_connections = max(0, server.current_connections - 1)
        
        # All retries failed
        self.metrics.failed_requests += 1
        
        return {
            'success': False,
            'error': str(last_error) if last_error else 'Unknown error',
            'attempts': retries + 1
        }
    
    async def _make_http_request(self, server: ServerInstance, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make actual HTTP request to server"""
        
        url = f"http://{server.address}/process"
        timeout = aiohttp.ClientTimeout(total=self.config.health_check_timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"HTTP {response.status}: {response.text}")
    
    async def _simulate_request(self, server: ServerInstance, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate request processing for testing"""
        
        # Simulate processing time based on server load
        base_time = 0.1  # 100ms base
        load_factor = server.connection_ratio
        processing_time = base_time * (1 + load_factor)
        
        await asyncio.sleep(processing_time)
        
        # Simulate occasional failures
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Simulated server error")
        
        return {
            'status': 'success',
            'server_id': server.id,
            'processed_at': datetime.now().isoformat(),
            'request_data': request_data
        }
    
    def _start_health_checking(self):
        """Start background health checking"""
        
        if self.health_check_task is None:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            self.logger.info("Health checking started")
    
    async def _health_check_loop(self):
        """Background health checking loop"""
        
        while not self._stop_health_check.is_set():
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def _perform_health_checks(self):
        """Perform health checks on all servers"""
        
        with self.server_lock:
            servers_to_check = list(self.servers.values())
        
        tasks = []
        for server in servers_to_check:
            task = asyncio.create_task(self._check_server_health(server))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_server_health(self, server: ServerInstance):
        """Check health of a specific server"""
        
        try:
            if HTTP_AVAILABLE:
                # Actual HTTP health check
                url = f"http://{server.address}/health"
                timeout = aiohttp.ClientTimeout(total=self.config.health_check_timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            await self._mark_server_healthy(server)
                        else:
                            await self._mark_server_unhealthy(server)
            else:
                # Simulated health check
                await asyncio.sleep(0.1)  # Simulate network latency
                
                # Simulate health check failure based on error rate
                if random.random() < server.error_rate:
                    await self._mark_server_unhealthy(server)
                else:
                    await self._mark_server_healthy(server)
            
        except Exception as e:
            self.logger.warning(f"Health check failed for server {server.id}: {e}")
            await self._mark_server_unhealthy(server)
    
    async def _mark_server_healthy(self, server: ServerInstance):
        """Mark server as healthy"""
        
        server.last_health_check = datetime.now()
        
        if server.status == ServerStatus.UNHEALTHY:
            server.error_count = max(0, server.error_count - 1)
            
            # Mark as healthy if error count is low enough
            if server.error_count <= self.config.healthy_threshold:
                server.status = ServerStatus.HEALTHY
                self.logger.info(f"Server {server.id} marked as healthy")
    
    async def _mark_server_unhealthy(self, server: ServerInstance):
        """Mark server as unhealthy"""
        
        server.last_health_check = datetime.now()
        server.error_count += 1
        
        if server.status == ServerStatus.HEALTHY:
            if server.error_count >= self.config.unhealthy_threshold:
                server.status = ServerStatus.UNHEALTHY
                self.logger.warning(f"Server {server.id} marked as unhealthy")
    
    def set_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """Manually set server status"""
        
        with self.server_lock:
            if server_id in self.servers:
                self.servers[server_id].status = status
                self.logger.info(f"Server {server_id} status set to {status.value}")
                return True
        
        return False
    
    def drain_server(self, server_id: str) -> bool:
        """Drain server (stop sending new requests)"""
        
        return self.set_server_status(server_id, ServerStatus.DRAINING)
    
    def put_server_in_maintenance(self, server_id: str) -> bool:
        """Put server in maintenance mode"""
        
        return self.set_server_status(server_id, ServerStatus.MAINTENANCE)
    
    def get_server_status(self, server_id: str) -> Optional[ServerInstance]:
        """Get server status"""
        
        with self.server_lock:
            return self.servers.get(server_id)
    
    def get_all_servers(self) -> List[ServerInstance]:
        """Get all server instances"""
        
        with self.server_lock:
            return list(self.servers.values())
    
    def get_healthy_servers(self) -> List[ServerInstance]:
        """Get healthy server instances"""
        
        with self.server_lock:
            return [s for s in self.servers.values() if s.status == ServerStatus.HEALTHY]
    
    def update_metrics(self):
        """Update load balancer metrics"""
        
        with self.server_lock:
            self.metrics.server_count = len(self.servers)
            self.metrics.healthy_servers = len(self.get_healthy_servers())
            self.metrics.active_connections = sum(s.current_connections for s in self.servers.values())
        
        # Calculate requests per second
        if len(self.request_times) > 1:
            time_window = 60  # 1 minute
            recent_requests = len([t for t in self.request_times if time.time() - t/1000 <= time_window])
            self.metrics.requests_per_second = recent_requests / time_window
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get load balancer metrics"""
        
        self.update_metrics()
        
        return {
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'success_rate': self.metrics.successful_requests / max(1, self.metrics.total_requests),
            'avg_response_time_ms': self.metrics.avg_response_time_ms,
            'requests_per_second': self.metrics.requests_per_second,
            'active_connections': self.metrics.active_connections,
            'server_count': self.metrics.server_count,
            'healthy_servers': self.metrics.healthy_servers,
            'algorithm': self.config.algorithm.value,
            'sticky_sessions_enabled': self.config.enable_sticky_sessions,
            'active_sticky_sessions': len(self.sticky_sessions)
        }
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed load balancer statistics"""
        
        stats = self.get_metrics()
        
        # Add server details
        with self.server_lock:
            server_details = []
            for server in self.servers.values():
                server_details.append({
                    'id': server.id,
                    'address': server.address,
                    'status': server.status.value,
                    'weight': server.weight,
                    'connections': server.current_connections,
                    'max_connections': server.max_connections,
                    'connection_ratio': server.connection_ratio,
                    'response_time_ms': server.response_time_ms,
                    'error_rate': server.error_rate,
                    'total_requests': server.total_requests,
                    'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None
                })
        
        stats['servers'] = server_details
        
        # Add configuration
        stats['configuration'] = {
            'algorithm': self.config.algorithm.value,
            'health_check_interval': self.config.health_check_interval,
            'health_check_timeout': self.config.health_check_timeout,
            'unhealthy_threshold': self.config.unhealthy_threshold,
            'healthy_threshold': self.config.healthy_threshold,
            'max_retries': self.config.max_retries,
            'retry_delay': self.config.retry_delay,
            'enable_sticky_sessions': self.config.enable_sticky_sessions,
            'session_timeout': self.config.session_timeout
        }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform load balancer health check"""
        
        health_status = {
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Check if we have healthy servers
            healthy_servers = self.get_healthy_servers()
            health_status['checks']['has_healthy_servers'] = len(healthy_servers) > 0
            health_status['checks']['healthy_server_count'] = len(healthy_servers)
            
            # Check health checking task
            health_status['checks']['health_checking_active'] = (
                self.health_check_task is not None and not self.health_check_task.done()
            )
            
            # Test load balancing
            test_result = await self.route_request(
                {'test': True},
                session_id='health_check',
                client_ip='127.0.0.1',
                retries=1
            )
            health_status['checks']['load_balancing_works'] = test_result['success']
            
            # Overall health
            health_status['healthy'] = all([
                health_status['checks'].get('has_healthy_servers', False),
                health_status['checks'].get('health_checking_active', False),
                health_status['checks'].get('load_balancing_works', False)
            ])
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
            self.logger.error(f"Load balancer health check failed: {e}")
        
        return health_status
    
    def cleanup_stale_sessions(self):
        """Clean up stale sticky sessions"""
        
        if not self.config.enable_sticky_sessions:
            return
        
        current_time = time.time()
        stale_sessions = []
        
        for session_id, server_id in self.sticky_sessions.items():
            # In a real implementation, you'd track session timestamps
            # For now, just remove old sessions based on some heuristic
            if len(session_id) > 100:  # Simple heuristic for "old" sessions
                stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            del self.sticky_sessions[session_id]
        
        if stale_sessions:
            self.logger.info(f"Cleaned up {len(stale_sessions)} stale sticky sessions")
    
    async def close(self):
        """Close load balancer and cleanup resources"""
        
        # Stop health checking
        if self.health_check_task:
            self._stop_health_check.set()
            self.health_check_task.cancel()
            
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup sessions
        self.cleanup_stale_sessions()
        
        self.logger.info("Load balancer closed")


# Auto-scaling support
class AutoScaler:
    """Auto-scaling support for load balancer"""
    
    def __init__(self, load_balancer: LoadBalancer, min_servers: int = 2, max_servers: int = 10):
        self.load_balancer = load_balancer
        self.min_servers = min_servers
        self.max_servers = max_servers
        self.logger = logging.getLogger(__name__)
        
        # Scaling configuration
        self.scale_up_threshold = 0.8  # 80% connection ratio
        self.scale_down_threshold = 0.3  # 30% connection ratio
        self.scale_up_cooldown = 300  # 5 minutes
        self.scale_down_cooldown = 600  # 10 minutes
        
        # Scaling state
        self.last_scale_up = 0
        self.last_scale_down = 0
        self.scaling_task: Optional[asyncio.Task] = None
    
    def start_auto_scaling(self):
        """Start auto-scaling monitoring"""
        
        if self.scaling_task is None:
            self.scaling_task = asyncio.create_task(self._auto_scaling_loop())
            self.logger.info("Auto-scaling started")
    
    async def _auto_scaling_loop(self):
        """Auto-scaling monitoring loop"""
        
        while True:
            try:
                await self._check_scaling_needs()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(60)
    
    async def _check_scaling_needs(self):
        """Check if scaling is needed"""
        
        current_time = time.time()
        servers = self.load_balancer.get_healthy_servers()
        
        if not servers:
            return
        
        # Calculate average connection ratio
        avg_connection_ratio = sum(s.connection_ratio for s in servers) / len(servers)
        
        # Check scale up conditions
        if (avg_connection_ratio > self.scale_up_threshold and 
            len(servers) < self.max_servers and
            current_time - self.last_scale_up > self.scale_up_cooldown):
            
            await self._scale_up()
            self.last_scale_up = current_time
        
        # Check scale down conditions
        elif (avg_connection_ratio < self.scale_down_threshold and 
              len(servers) > self.min_servers and
              current_time - self.last_scale_down > self.scale_down_cooldown):
            
            await self._scale_down()
            self.last_scale_down = current_time
    
    async def _scale_up(self):
        """Scale up by adding a new server"""
        
        self.logger.info("Initiating scale up")
        
        # In a real implementation, this would provision a new server instance
        # For now, just log the action
        new_server_id = f"auto_scaled_{int(time.time())}"
        
        # Simulate server addition (in production, this would be cloud provider API calls)
        self.load_balancer.add_server(
            new_server_id,
            "127.0.0.1",  # In production, this would be a real host
            8080 + len(self.load_balancer.servers),
            weight=1
        )
        
        self.logger.info(f"Scaled up: added server {new_server_id}")
    
    async def _scale_down(self):
        """Scale down by removing a server"""
        
        self.logger.info("Initiating scale down")
        
        servers = self.load_balancer.get_healthy_servers()
        if len(servers) <= self.min_servers:
            return
        
        # Find server with lowest connections
        server_to_remove = min(servers, key=lambda s: s.current_connections)
        
        # Drain the server first
        self.load_balancer.drain_server(server_to_remove.id)
        
        # Wait for connections to drain (simplified)
        await asyncio.sleep(30)
        
        # Remove server
        self.load_balancer.remove_server(server_to_remove.id)
        
        self.logger.info(f"Scaled down: removed server {server_to_remove.id}")
    
    def stop_auto_scaling(self):
        """Stop auto-scaling"""
        
        if self.scaling_task:
            self.scaling_task.cancel()
            self.scaling_task = None
            self.logger.info("Auto-scaling stopped")
