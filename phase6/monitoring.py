"""
Monitoring and Health Checks System

Provides comprehensive monitoring, health checks, metrics collection,
and alerting for the production backend infrastructure.
"""

import asyncio
import logging
import time
import psutil
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque

# Import Phase 5 components for integration
try:
    from ..phase5.logger import SystemLogger
    from ..phase5.monitoring import ErrorTracker
    from ..phase5.metrics import MetricsCollector
except ImportError:
    from phase5.logger import SystemLogger
    from phase5.monitoring import ErrorTracker
    from phase5.metrics import MetricsCollector


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    description: str
    check_function: Callable
    interval: int = 60  # seconds
    timeout: int = 10   # seconds
    enabled: bool = True
    critical: bool = False


@dataclass
class HealthCheckResult:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: Optional[List[float]] = None
    uptime_seconds: float = 0.0


@dataclass
class Alert:
    """Alert definition"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self, component_name: str = "phase6_backend"):
        self.component_name = component_name
        self.logger = logging.getLogger(__name__)
        
        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, HealthCheckResult] = {}
        self.check_tasks: Dict[str, asyncio.Task] = {}
        
        # Metrics
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 data points
        self.alerts: List[Alert] = []
        
        # Monitoring state
        self.start_time = datetime.now()
        self._stop_monitoring = asyncio.Event()
        
        # Callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Initialize default health checks
        self._setup_default_health_checks()
        
        # Start monitoring
        self._start_monitoring()
    
    def set_cache_manager(self, cache_manager):
        """Set cache manager for integration"""
        self.cache_manager = cache_manager
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        
        # Database health check
        self.add_health_check(HealthCheck(
            name="database",
            description="Database connectivity and performance",
            check_function=self._check_database_health,
            interval=30,
            timeout=5,
            critical=True
        ))
        
        # Cache health check
        self.add_health_check(HealthCheck(
            name="cache",
            description="Cache system health",
            check_function=self._check_cache_health,
            interval=60,
            timeout=5
        ))
        
        # System resources health check
        self.add_health_check(HealthCheck(
            name="system_resources",
            description="System resource usage",
            check_function=self._check_system_resources,
            interval=30,
            timeout=5
        ))
        
        # API Gateway health check
        self.add_health_check(HealthCheck(
            name="api_gateway",
            description="API Gateway functionality",
            check_function=self._check_api_gateway_health,
            interval=30,
            timeout=10,
            critical=True
        ))
        
        # Authentication health check
        self.add_health_check(HealthCheck(
            name="authentication",
            description="Authentication system health",
            check_function=self._check_authentication_health,
            interval=60,
            timeout=5
        ))
        
        # Rate limiting health check
        self.add_health_check(HealthCheck(
            name="rate_limiting",
            description="Rate limiting system health",
            check_function=self._check_rate_limiting_health,
            interval=60,
            timeout=5
        ))
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a health check"""
        
        self.health_checks[health_check.name] = health_check
        
        # Start the check if monitoring is active
        if not self._stop_monitoring.is_set():
            self._start_health_check(health_check)
        
        self.logger.info(f"Added health check: {health_check.name}")
    
    def remove_health_check(self, name: str) -> bool:
        """Remove a health check"""
        
        if name in self.health_checks:
            # Stop the check task
            if name in self.check_tasks:
                self.check_tasks[name].cancel()
                del self.check_tasks[name]
            
            del self.health_checks[name]
            
            # Remove results
            if name in self.health_results:
                del self.health_results[name]
            
            self.logger.info(f"Removed health check: {name}")
            return True
        
        return False
    
    def _start_health_check(self, health_check: HealthCheck):
        """Start a health check task"""
        
        if health_check.name in self.check_tasks:
            return  # Already running
        
        task = asyncio.create_task(self._run_health_check(health_check))
        self.check_tasks[health_check.name] = task
    
    def _start_monitoring(self):
        """Start all health monitoring"""
        
        for health_check in self.health_checks.values():
            if health_check.enabled:
                self._start_health_check(health_check)
        
        self.logger.info("Health monitoring started")
    
    async def _run_health_check(self, health_check: HealthCheck):
        """Run a health check continuously"""
        
        while not self._stop_monitoring.is_set():
            try:
                if health_check.enabled:
                    result = await self._execute_health_check(health_check)
                    self.health_results[health_check.name] = result
                    
                    # Check for alerts
                    await self._check_for_alerts(result)
                
                # Wait for next check
                await asyncio.sleep(health_check.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check {health_check.name} error: {e}")
                await asyncio.sleep(health_check.interval)
    
    async def _execute_health_check(self, health_check: HealthCheck) -> HealthCheckResult:
        """Execute a single health check"""
        
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                return result
            elif isinstance(result, bool):
                return HealthCheckResult(
                    name=health_check.name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message="Check passed" if result else "Check failed",
                    timestamp=datetime.now(),
                    duration_ms=duration_ms
                )
            elif isinstance(result, dict):
                status = HealthStatus(result.get('status', 'healthy'))
                return HealthCheckResult(
                    name=health_check.name,
                    status=status,
                    message=result.get('message', ''),
                    timestamp=datetime.now(),
                    duration_ms=duration_ms,
                    details=result.get('details'),
                    error=result.get('error')
                )
            else:
                return HealthCheckResult(
                    name=health_check.name,
                    status=HealthStatus.HEALTHY,
                    message=str(result),
                    timestamp=datetime.now(),
                    duration_ms=duration_ms
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=health_check.name,
                status=HealthStatus.UNHEALTHY,
                message="Health check timeout",
                timestamp=datetime.now(),
                duration_ms=health_check.timeout * 1000,
                error="Timeout"
            )
        except Exception as e:
            return HealthCheckResult(
                name=health_check.name,
                status=HealthStatus.UNHEALTHY,
                message="Health check failed",
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    # Default health check implementations
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        
        try:
            # Try to import and check database manager
            from .database import DatabaseManager, DatabaseConfig
            
            # Create a simple test connection
            config = DatabaseConfig(db_type="sqlite", database="health_check")
            db_manager = DatabaseManager(config)
            
            # Test query
            result = db_manager.execute_query("SELECT 1")
            
            # Get database stats
            stats = db_manager.get_database_stats()
            
            db_manager.close()
            
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'details': {
                    'test_query_success': True,
                    'database_stats': stats
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error': str(e)
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health"""
        
        try:
            from .cache import CacheManager, CacheConfig
            
            config = CacheConfig(backend="memory")
            cache_manager = CacheManager(config)
            
            # Test cache operations
            test_key = f"health_check_{int(time.time())}"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Test set
            set_success = await cache_manager.set(test_key, test_value, 60)
            
            # Test get
            retrieved_value = await cache_manager.get(test_key)
            
            # Test delete
            delete_success = await cache_manager.delete(test_key)
            
            # Get cache metrics
            metrics = cache_manager.get_metrics()
            
            cache_manager.close()
            
            if set_success and retrieved_value == test_value and delete_success:
                return {
                    'status': 'healthy',
                    'message': 'Cache operations successful',
                    'details': {
                        'cache_metrics': metrics
                    }
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Cache operations failed',
                    'details': {
                        'set_success': set_success,
                        'get_success': retrieved_value == test_value,
                        'delete_success': delete_success
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'Cache health check failed',
                'error': str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            load_average = None
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                pass  # Not available on Windows
            
            # Determine status
            status = 'healthy'
            warnings = []
            
            if cpu_percent > 90:
                status = 'critical'
                warnings.append('High CPU usage')
            elif cpu_percent > 80:
                status = 'degraded'
                warnings.append('Elevated CPU usage')
            
            if memory_percent > 90:
                status = 'critical'
                warnings.append('High memory usage')
            elif memory_percent > 80:
                status = 'degraded' if status == 'healthy' else status
                warnings.append('Elevated memory usage')
            
            if disk_usage_percent > 90:
                status = 'critical'
                warnings.append('High disk usage')
            elif disk_usage_percent > 80:
                status = 'degraded' if status == 'healthy' else status
                warnings.append('Elevated disk usage')
            
            # Store metrics
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average,
                uptime_seconds=time.time() - self.start_time.timestamp()
            )
            
            self.metrics_history.append(metrics)
            
            return {
                'status': status,
                'message': f"System resources {'ok' if status == 'healthy' else ', '.join(warnings)}",
                'details': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_usage_percent': disk_usage_percent,
                    'network_io': network_io,
                    'process_count': process_count,
                    'load_average': load_average,
                    'uptime_seconds': metrics.uptime_seconds
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'System resource check failed',
                'error': str(e)
            }
    
    async def _check_api_gateway_health(self) -> Dict[str, Any]:
        """Check API Gateway health"""
        
        try:
            from .api_gateway import APIGateway
            
            gateway = APIGateway()
            
            # Test health check endpoint
            response = await gateway.handle_request('GET', '/health')
            
            if response.get('status') == 200 and response.get('healthy', False):
                return {
                    'status': 'healthy',
                    'message': 'API Gateway healthy',
                    'details': {
                        'response': response
                    }
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'API Gateway health check failed',
                    'details': {
                        'response': response
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'API Gateway health check failed',
                'error': str(e)
            }
    
    async def _check_authentication_health(self) -> Dict[str, Any]:
        """Check authentication system health"""
        
        try:
            from .auth import AuthManager, AuthConfig
            
            config = AuthConfig()
            auth_manager = AuthManager(config)
            
            # Test authentication
            result = await auth_manager.health_check()
            
            return result
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'Authentication health check failed',
                'error': str(e)
            }
    
    async def _check_rate_limiting_health(self) -> Dict[str, Any]:
        """Check rate limiting system health"""
        
        try:
            from .rate_limiter import RateLimiter
            
            rate_limiter = RateLimiter()
            
            # Test rate limiting
            result = await rate_limiter.health_check()
            
            return result
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': 'Rate limiting health check failed',
                'error': str(e)
            }
    
    async def _check_for_alerts(self, result: HealthCheckResult):
        """Check if health check result should trigger alerts"""
        
        # Critical failure alert
        if result.status == HealthStatus.CRITICAL:
            await self._create_alert(
                AlertSeverity.CRITICAL,
                f"Critical health check failure: {result.name}",
                f"Health check {result.name} failed critically: {result.message}",
                result.name,
                {'result': asdict(result)}
            )
        
        # Unhealthy critical check alert
        elif (result.status == HealthStatus.UNHEALTHY and 
              self.health_checks.get(result.name, HealthCheck("", "", lambda: None)).critical):
            await self._create_alert(
                AlertSeverity.ERROR,
                f"Critical health check unhealthy: {result.name}",
                f"Critical health check {result.name} is unhealthy: {result.message}",
                result.name,
                {'result': asdict(result)}
            )
        
        # Degraded performance alert
        elif result.status == HealthStatus.DEGRADED:
            await self._create_alert(
                AlertSeverity.WARNING,
                f"Degraded performance: {result.name}",
                f"Health check {result.name} shows degraded performance: {result.message}",
                result.name,
                {'result': asdict(result)}
            )
    
    async def _create_alert(self, severity: AlertSeverity, title: str, message: str, 
                           source: str, details: Optional[Dict[str, Any]] = None):
        """Create and handle an alert"""
        
        alert = Alert(
            id=f"alert_{int(time.time() * 1000)}",
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            details=details
        )
        
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
        
        self.logger.warning(f"Alert created: {severity.value.upper()} - {title}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        
        self.alert_callbacks.append(callback)
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        
        if not self.health_results:
            return {
                'status': 'unknown',
                'message': 'No health check results available',
                'timestamp': datetime.now().isoformat(),
                'checks': {}
            }
        
        # Determine overall status
        critical_failures = [
            name for name, result in self.health_results.items()
            if result.status == HealthStatus.CRITICAL
        ]
        
        unhealthy_critical = [
            name for name, result in self.health_results.items()
            if (result.status == HealthStatus.UNHEALTHY and 
                self.health_checks.get(name, HealthCheck("", "", lambda: None)).critical)
        ]
        
        unhealthy_checks = [
            name for name, result in self.health_results.items()
            if result.status == HealthStatus.UNHEALTHY
        ]
        
        degraded_checks = [
            name for name, result in self.health_results.items()
            if result.status == HealthStatus.DEGRADED
        ]
        
        # Determine overall status
        if critical_failures:
            overall_status = 'critical'
            message = f"Critical failures in: {', '.join(critical_failures)}"
        elif unhealthy_critical:
            overall_status = 'unhealthy'
            message = f"Critical checks unhealthy: {', '.join(unhealthy_critical)}"
        elif unhealthy_checks:
            overall_status = 'unhealthy'
            message = f"Unhealthy checks: {', '.join(unhealthy_checks)}"
        elif degraded_checks:
            overall_status = 'degraded'
            message = f"Degraded checks: {', '.join(degraded_checks)}"
        else:
            overall_status = 'healthy'
            message = "All health checks passing"
        
        # Compile check results
        checks = {}
        for name, result in self.health_results.items():
            checks[name] = {
                'status': result.status.value,
                'message': result.message,
                'timestamp': result.timestamp.isoformat(),
                'duration_ms': result.duration_ms,
                'critical': self.health_checks.get(name, HealthCheck("", "", lambda: None)).critical
            }
        
        return {
            'status': overall_status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'checks': checks,
            'summary': {
                'total_checks': len(self.health_results),
                'healthy': len([r for r in self.health_results.values() if r.status == HealthStatus.HEALTHY]),
                'degraded': len(degraded_checks),
                'unhealthy': len(unhealthy_checks),
                'critical': len(critical_failures)
            }
        }
    
    def get_health_check_results(self) -> Dict[str, Any]:
        """Get all health check results"""
        
        results = {}
        for name, result in self.health_results.items():
            results[name] = asdict(result)
        
        return results
    
    def get_system_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        
        recent_metrics = list(self.metrics_history)[-limit:]
        return [asdict(metric) for metric in recent_metrics]
    
    def get_alerts(self, severity: Optional[AlertSeverity] = None, 
                  resolved: Optional[bool] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        
        alerts = self.alerts
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        # Return most recent
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]
        
        return [asdict(alert) for alert in alerts]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self.logger.info(f"Alert resolved: {alert_id}")
                return True
        
        return False
    
    async def run_health_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check manually"""
        
        if name not in self.health_checks:
            return None
        
        health_check = self.health_checks[name]
        return await self._execute_health_check(health_check)
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks manually"""
        
        results = {}
        tasks = []
        
        for health_check in self.health_checks.values():
            if health_check.enabled:
                task = asyncio.create_task(self._execute_health_check(health_check))
                tasks.append((health_check.name, task))
        
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                self.health_results[name] = result
            except Exception as e:
                self.logger.error(f"Manual health check {name} failed: {e}")
        
        return results
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        
        return {
            'component_name': self.component_name,
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'health_checks_count': len(self.health_checks),
            'enabled_health_checks': len([c for c in self.health_checks.values() if c.enabled]),
            'critical_health_checks': len([c for c in self.health_checks.values() if c.critical]),
            'total_alerts': len(self.alerts),
            'unresolved_alerts': len([a for a in self.alerts if not a.resolved]),
            'metrics_points': len(self.metrics_history),
            'alert_callbacks': len(self.alert_callbacks)
        }
    
    async def stop_monitoring(self):
        """Stop all health monitoring"""
        
        self._stop_monitoring.set()
        
        # Cancel all health check tasks
        for task in self.check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.check_tasks:
            await asyncio.gather(*self.check_tasks.values(), return_exceptions=True)
        
        self.check_tasks.clear()
        self.logger.info("Health monitoring stopped")


# Alert callback examples
class LoggingAlertCallback:
    """Callback to log alerts"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def __call__(self, alert: Alert):
        """Log alert"""
        
        level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        self.logger.log(level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")


class MetricsAlertCallback:
    """Callback to update metrics on alerts"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics_collector = metrics_collector
    
    def __call__(self, alert: Alert):
        """Record alert in metrics"""
        
        if self.metrics_collector:
            self.metrics_collector.record_metric(
                f"alert_{alert.severity.value}",
                1,
                "count",
                "monitoring",
                {
                    'alert_id': alert.id,
                    'source': alert.source,
                    'title': alert.title
                }
            )
