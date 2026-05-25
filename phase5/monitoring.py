"""
Error Tracking and Monitoring System

Provides comprehensive error tracking, monitoring, and alerting
for the restaurant recommendation system.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

# Import from previous phases
try:
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase3.output_validator import RecommendationResponse
except ImportError:
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase3.output_validator import RecommendationResponse


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Represents an error event"""
    timestamp: str
    error_id: str
    severity: ErrorSeverity
    component: str
    error_type: str
    message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Represents a performance metric"""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    component: str
    threshold: Optional[float] = None
    alert_threshold: Optional[float] = None


class ErrorTracker:
    """Centralized error tracking and monitoring system"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.logger = logging.getLogger(__name__)
        self.errors: List[ErrorEvent] = []
        self.metrics: List[PerformanceMetric] = []
        self.alert_thresholds = alert_thresholds or {
            'error_rate': 0.05,  # 5% error rate
            'response_time': 5000,  # 5 seconds
            'memory_usage': 0.8,  # 80% memory usage
            'cpu_usage': 0.8  # 80% CPU usage
        }
        self.error_counts: Dict[str, int] = {}
        self.performance_history: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        self._load_persisted_data()
    
    def _load_persisted_data(self):
        """Load persisted error and metric data"""
        try:
            # Load errors
            error_file = "phase5_errors.json"
            if os.path.exists(error_file):
                with open(error_file, 'r') as f:
                    error_data = json.load(f)
                    self.errors = [ErrorEvent(**error) for error in error_data.get('errors', [])]
            
            # Load metrics
            metrics_file = "phase5_metrics.json"
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    self.metrics = [PerformanceMetric(**metric) for metric in metrics_data.get('metrics', [])]
                    
        except Exception as e:
            self.logger.error(f"Failed to load persisted data: {e}")
    
    def track_error(self, error_type: str, message: str, component: str,
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                  context: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None,
                  user_id: Optional[str] = None,
                  request_id: Optional[str] = None):
        """Track a new error event"""
        
        with self.lock:
            error_id = f"err_{int(time.time() * 1000):06d}"
            
            error_event = ErrorEvent(
                timestamp=datetime.now().isoformat(),
                error_id=error_id,
                severity=severity,
                component=component,
                error_type=error_type,
                message=message,
                context=context or {},
                stack_trace=stack_trace,
                user_id=user_id,
                request_id=request_id
            )
            
            self.errors.append(error_event)
            self.error_counts[component] = self.error_counts.get(component, 0) + 1
            
            # Log the error
            self.logger.error(f"[{component}] {severity.value.upper()}: {message}")
            
            # Check for alerts
            self._check_error_alerts(error_event)
            
            # Persist immediately
            self._persist_errors()
    
    def track_performance(self, metric_name: str, value: float, unit: str,
                        component: str, threshold: Optional[float] = None,
                        alert_threshold: Optional[float] = None):
        """Track a performance metric"""
        
        with self.lock:
            metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=metric_name,
                value=value,
                unit=unit,
                component=component,
                threshold=threshold,
                alert_threshold=alert_threshold
            )
            
            self.metrics.append(metric)
            
            # Update performance history
            if component not in self.performance_history:
                self.performance_history[component] = []
            self.performance_history[component].append(value)
            
            # Keep only last 100 values
            if len(self.performance_history[component]) > 100:
                self.performance_history[component] = self.performance_history[component][-100:]
            
            # Log the metric
            self.logger.info(f"[{component}] {metric_name}: {value} {unit}")
            
            # Check for alerts
            self._check_performance_alerts(metric)
            
            # Persist periodically
            if len(self.metrics) % 10 == 0:
                self._persist_metrics()
    
    def resolve_error(self, error_id: str, resolution: str):
        """Mark an error as resolved"""
        
        with self.lock:
            for error in self.errors:
                if error.error_id == error_id:
                    error.resolved = True
                    error.resolution_time = datetime.now().isoformat()
                    
                    self.logger.info(f"Resolved error {error_id}: {resolution}")
                    break
            
            self._persist_errors()
    
    def get_error_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error summary for time window"""
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_errors = [
            error for error in self.errors
            if datetime.fromisoformat(error.timestamp) > cutoff_time
        ]
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in recent_errors if error.severity == severity
            )
        
        # Count by component
        component_counts = {}
        for error in recent_errors:
            component_counts[error.component] = component_counts.get(error.component, 0) + 1
        
        # Calculate error rate
        total_errors = len(recent_errors)
        error_rate = total_errors / (time_window_hours * 60) if time_window_hours > 0 else 0
        
        return {
            "time_window_hours": time_window_hours,
            "total_errors": total_errors,
            "error_rate_per_hour": error_rate,
            "severity_breakdown": severity_counts,
            "component_breakdown": component_counts,
            "unresolved_errors": len([e for e in recent_errors if not e.resolved]),
            "critical_errors": len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
        }
    
    def get_performance_summary(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary"""
        
        summary = {
            "total_metrics": len(self.metrics),
            "components": list(set(m.component for m in self.metrics)),
            "metric_names": list(set(m.metric_name for m in self.metrics))
        }
        
        if component and component in self.performance_history:
            values = self.performance_history[component]
            if values:
                summary[component] = {
                    "current": values[-1],
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "trend": "improving" if len(values) > 1 and values[-1] < values[-2] else "stable",
                    "sample_size": len(values)
                }
        
        return summary
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        
        error_summary = self.get_error_summary()
        performance_summary = self.get_performance_summary()
        
        # Determine health status
        health_status = "healthy"
        health_issues = []
        
        if error_summary["critical_errors"] > 0:
            health_status = "critical"
            health_issues.append(f"{error_summary['critical_errors']} critical errors")
        elif error_summary["error_rate_per_hour"] > self.alert_thresholds.get("error_rate", 0.05):
            health_status = "degraded"
            health_issues.append(f"High error rate: {error_summary['error_rate_per_hour']:.2f}/hour")
        elif error_summary["unresolved_errors"] > 10:
            health_status = "warning"
            health_issues.append(f"{error_summary['unresolved_errors']} unresolved errors")
        
        return {
            "status": health_status,
            "issues": health_issues,
            "error_summary": error_summary,
            "performance_summary": performance_summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_error_alerts(self, error_event: ErrorEvent):
        """Check if error triggers alerts"""
        
        # Critical errors always alert
        if error_event.severity == ErrorSeverity.CRITICAL:
            self._send_alert(
                alert_type="critical_error",
                message=f"Critical error in {error_event.component}: {error_event.message}",
                severity=error_event.severity.value,
                data=asdict(error_event)
            )
        
        # Check error rate threshold
        error_summary = self.get_error_summary(1)  # Last hour
        if error_summary["error_rate_per_hour"] > self.alert_thresholds.get("error_rate", 0.05):
            self._send_alert(
                alert_type="high_error_rate",
                message=f"High error rate detected: {error_summary['error_rate_per_hour']:.2f}/hour",
                severity="high",
                data=error_summary
            )
    
    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if performance metric triggers alerts"""
        
        if metric.alert_threshold and metric.value > metric.alert_threshold:
            self._send_alert(
                alert_type="performance_threshold",
                message=f"Performance threshold exceeded: {metric.metric_name} = {metric.value} {metric.unit}",
                severity="medium",
                data=asdict(metric)
            )
        
        if metric.threshold and metric.value > metric.threshold:
            self._send_alert(
                alert_type="performance_threshold",
                message=f"Performance threshold exceeded: {metric.metric_name} = {metric.value} {metric.unit}",
                severity="medium",
                data=asdict(metric)
            )
    
    def _send_alert(self, alert_type: str, message: str, severity: str, data: Dict[str, Any]):
        """Send alert (placeholder for actual alerting system)"""
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "data": data
        }
        
        # Log alert
        self.logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
        
        # In a real system, this would send to monitoring service
        # For now, just log to file
        self._persist_alert(alert)
    
    def _persist_errors(self):
        """Persist errors to file"""
        try:
            error_file = "phase5_errors.json"
            with open(error_file, 'w') as f:
                json.dump({
                    "errors": [asdict(error) for error in self.errors[-1000:]]  # Keep last 1000 errors
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to persist errors: {e}")
    
    def _persist_metrics(self):
        """Persist metrics to file"""
        try:
            metrics_file = "phase5_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump({
                    "metrics": [asdict(metric) for metric in self.metrics[-1000:]]  # Keep last 1000 metrics
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to persist metrics: {e}")
    
    def _persist_alert(self, alert: Dict[str, Any]):
        """Persist alert to file"""
        try:
            alert_file = "phase5_alerts.json"
            alerts = []
            
            # Load existing alerts
            if os.path.exists(alert_file):
                with open(alert_file, 'r') as f:
                    alerts = json.load(f).get('alerts', [])
            
            alerts.append(alert)
            
            # Keep only last 100 alerts
            alerts = alerts[-100:]
            
            with open(alert_file, 'w') as f:
                json.dump({"alerts": alerts}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to persist alert: {e}")
    
    def export_monitoring_data(self, output_dir: str):
        """Export all monitoring data for analysis"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export errors
        self._persist_errors()
        error_file = os.path.join(output_dir, "phase5_errors.json")
        if os.path.exists("phase5_errors.json"):
            import shutil
            shutil.copy("phase5_errors.json", error_file)
        
        # Export metrics
        self._persist_metrics()
        metrics_file = os.path.join(output_dir, "phase5_metrics.json")
        if os.path.exists("phase5_metrics.json"):
            import shutil
            shutil.copy("phase5_metrics.json", metrics_file)
        
        # Export alerts
        alert_file = os.path.join(output_dir, "phase5_alerts.json")
        if os.path.exists("phase5_alerts.json"):
            import shutil
            shutil.copy("phase5_alerts.json", alert_file)
        
        self.logger.info(f"Monitoring data exported to: {output_dir}")
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over specified days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_errors = [
            error for error in self.errors
            if datetime.fromisoformat(error.timestamp) > cutoff_date
        ]
        
        # Group by day
        daily_errors = {}
        for error in recent_errors:
            day = error.timestamp.split('T')[0]  # Extract date part
            daily_errors[day] = daily_errors.get(day, 0) + 1
        
        # Calculate trends
        trend_data = []
        for day in sorted(daily_errors.keys()):
            trend_data.append({
                "date": day,
                "error_count": daily_errors[day],
                "severity_breakdown": {}
            })
        
        return {
            "period_days": days,
            "daily_errors": daily_errors,
            "trend_data": trend_data,
            "total_errors": len(recent_errors)
        }
