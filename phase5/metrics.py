"""
Metrics Collection for Restaurant Recommendation System

Collects and analyzes performance metrics for system evaluation.
"""

import json
import time
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Import from previous phases
try:
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase3.output_validator import RecommendationResponse, RestaurantRanking
except ImportError:
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase3.output_validator import RecommendationResponse, RestaurantRanking


@dataclass
class MetricValue:
    """Represents a single metric value"""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    component: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class MetricsSummary:
    """Represents a summary of metrics"""
    metric_name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    std_deviation: float
    trend: str
    unit: str


class MetricsCollector:
    """Collects and analyzes system performance metrics"""
    
    def __init__(self):
        self.metrics: List[MetricValue] = []
        self.start_time = datetime.now()
    
    def record_metric(self, metric_name: str, value: float, unit: str,
                   component: str, context: Optional[Dict[str, Any]] = None):
        """Record a metric value"""
        
        metric = MetricValue(
            timestamp=datetime.now().isoformat(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            component=component,
            context=context
        )
        
        self.metrics.append(metric)
    
    def record_latency(self, component: str, operation: str, latency_ms: float,
                    context: Optional[Dict[str, Any]] = None):
        """Record latency metric"""
        self.record_metric(
            metric_name=f"{operation}_latency",
            value=latency_ms,
            unit="ms",
            component=component,
            context=context
        )
    
    def record_throughput(self, component: str, operation: str, 
                         requests_per_second: float,
                         context: Optional[Dict[str, Any]] = None):
        """Record throughput metric"""
        self.record_metric(
            metric_name=f"{operation}_throughput",
            value=requests_per_second,
            unit="req/s",
            component=component,
            context=context
        )
    
    def record_error_rate(self, component: str, window_minutes: int, 
                        errors_per_minute: float,
                        context: Optional[Dict[str, Any]] = None):
        """Record error rate metric"""
        self.record_metric(
            metric_name="error_rate",
            value=errors_per_minute,
            unit="err/min",
            component=component,
            context={**context, "window_minutes": window_minutes}
        )
    
    def record_success_rate(self, component: str, window_minutes: int,
                          success_rate: float,
                          context: Optional[Dict[str, Any]] = None):
        """Record success rate metric"""
        self.record_metric(
            metric_name="success_rate",
            value=success_rate,
            unit="%",
            component=component,
            context={**context, "window_minutes": window_minutes}
        )
    
    def record_memory_usage(self, component: str, memory_mb: float,
                         context: Optional[Dict[str, Any]] = None):
        """Record memory usage metric"""
        self.record_metric(
            metric_name="memory_usage",
            value=memory_mb,
            unit="MB",
            component=component,
            context=context
        )
    
    def record_cpu_usage(self, component: str, cpu_percent: float,
                      context: Optional[Dict[str, Any]] = None):
        """Record CPU usage metric"""
        self.record_metric(
            metric_name="cpu_usage",
            value=cpu_percent,
            unit="%",
            component=component,
            context=context
        )
    
    def record_recommendation_quality(self, response: RecommendationResponse,
                                 preferences: UserPreferences,
                                 candidates: List[RestaurantCandidate]):
        """Record recommendation quality metrics"""
        
        if not response.rankings:
            return
        
        # Relevance score distribution
        scores = [r.relevance_score for r in response.rankings]
        if scores:
            avg_relevance = statistics.mean(scores)
            relevance_std = statistics.stdev(scores) if len(scores) > 1 else 0
            
            self.record_metric(
                metric_name="avg_relevance_score",
                value=avg_relevance,
                unit="score",
                component="llm_orchestrator"
            )
            
            self.record_metric(
                metric_name="relevance_score_std",
                value=relevance_std,
                unit="score",
                component="llm_orchestrator"
            )
        
        # Ranking consistency
        expected_ranks = list(range(1, len(response.rankings) + 1))
        actual_ranks = [r.rank for r in response.rankings]
        rank_consistency = len(set(actual_ranks) - set(expected_ranks)) == 0
        
        self.record_metric(
            metric_name="ranking_consistency",
            value=1.0 if rank_consistency else 0.0,
            unit="score",
            component="llm_orchestrator",
            context={
                "expected_ranks": expected_ranks,
                "actual_ranks": actual_ranks
            }
        )
        
        # Explanation quality
        explanation_lengths = [len(r.explanation) for r in response.rankings]
        if explanation_lengths:
            avg_explanation_length = statistics.mean(explanation_lengths)
            
            self.record_metric(
                metric_name="avg_explanation_length",
                value=avg_explanation_length,
                unit="chars",
                component="llm_orchestrator"
            )
        
        # Constraint satisfaction rate
        total_constraints = 4  # location, budget, cuisine, rating
        satisfied_constraints = 0
        
        # Check if recommendations respect constraints
        if response.rankings:
            # This would need actual constraint checking logic
            # For now, assume 75% satisfaction rate
            satisfied_constraints = int(total_constraints * 0.75)
        
        constraint_satisfaction_rate = satisfied_constraints / total_constraints if total_constraints > 0 else 0
        
        self.record_metric(
            metric_name="constraint_satisfaction_rate",
            value=constraint_satisfaction_rate,
            unit="%",
            component="system"
        )
    
    def record_diversity_metrics(self, response: RecommendationResponse,
                                candidates: List[RestaurantCandidate]):
        """Record diversity metrics"""
        
        if not response.rankings:
            return
        
        # Cuisine diversity
        cuisine_types = []
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                cuisine_types.extend(candidate.cuisines)
        
        unique_cuisines = len(set(cuisine_types))
        total_cuisines = len(cuisine_types)
        cuisine_diversity = unique_cuisines / total_cuisines if total_cuisines > 0 else 0
        
        self.record_metric(
            metric_name="cuisine_diversity",
            value=cuisine_diversity,
            unit="ratio",
            component="system"
        )
        
        # Price diversity
        prices = []
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                prices.append(candidate.cost_for_two)
        
        if prices:
            price_range = max(prices) - min(prices)
            avg_price = statistics.mean(prices)
            price_diversity = price_range / avg_price if avg_price > 0 else 0
            
            self.record_metric(
                metric_name="price_diversity",
                value=price_diversity,
                unit="ratio",
                component="system"
            )
    
    def get_metric_summary(self, metric_name: str, 
                         component: Optional[str] = None,
                         time_window_hours: int = 24) -> Optional[MetricsSummary]:
        """Get summary statistics for a specific metric"""
        
        # Filter metrics by name and component
        filtered_metrics = [
            m for m in self.metrics 
            if m.metric_name == metric_name and 
            (component is None or m.component == component)
        ]
        
        if not filtered_metrics:
            return None
        
        # Filter by time window
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_metrics = [
            m for m in filtered_metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        values = [m.value for m in recent_metrics]
        if not values:
            return None
        
        # Calculate statistics
        return MetricsSummary(
            metric_name=metric_name,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=statistics.median(values),
            std_deviation=statistics.stdev(values) if len(values) > 1 else 0,
            trend=self._calculate_trend(values),
            unit=recent_metrics[0].unit
        )
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.05:  # 5% increase
            return "improving"
        elif second_avg < first_avg * 0.95:  # 5% decrease
            return "degrading"
        else:
            return "stable"
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get overview of all system metrics"""
        
        # Group metrics by component
        component_metrics = {}
        for metric in self.metrics:
            if metric.component not in component_metrics:
                component_metrics[metric.component] = []
            component_metrics[metric.component].append(metric)
        
        # Calculate uptime
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return {
            "uptime_hours": uptime_hours,
            "total_metrics": len(self.metrics),
            "components": list(component_metrics.keys()),
            "metric_types": list(set(m.metric_name for m in self.metrics)),
            "data_collection_period": {
                "start": self.start_time.isoformat(),
                "end": datetime.now().isoformat()
            }
        }
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        
        try:
            metrics_data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics": [asdict(m) for m in self.metrics],
                "system_overview": self.get_system_overview()
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            print(f"📊 Metrics exported to: {filepath}")
            
        except Exception as e:
            print(f"❌ Failed to export metrics: {e}")
    
    def get_baseline_metrics(self) -> Dict[str, Any]:
        """Get baseline metrics for comparison"""
        
        # Define baseline targets
        baseline_targets = {
            "llm_latency_ms": 2000,  # 2 seconds
            "api_latency_ms": 500,    # 0.5 seconds
            "error_rate": 0.02,    # 2%
            "success_rate": 0.98,    # 98%
            "memory_usage_mb": 512,   # 512MB
            "cpu_usage_percent": 70,    # 70%
            "avg_relevance_score": 80,   # 80/100
            "cuisine_diversity": 0.6,   # 60%
            "constraint_satisfaction_rate": 0.9  # 90%
        }
        
        # Calculate current metrics
        current_metrics = {}
        for metric_name, target in baseline_targets.items():
            summary = self.get_metric_summary(metric_name)
            if summary:
                current_metrics[metric_name] = {
                    "current": summary.avg_value,
                    "target": target,
                    "status": "good" if self._is_metric_good(metric_name, summary.avg_value, target) else "needs_improvement",
                    "deviation_percent": abs(summary.avg_value - target) / target * 100
                }
        
        return {
            "baseline_targets": baseline_targets,
            "current_metrics": current_metrics,
            "overall_health": "good" if all(
                m.get("status") == "good" for m in current_metrics.values()
            ) else "needs_attention"
        }
    
    def _is_metric_good(self, metric_name: str, current_value: float, target: float) -> bool:
        """Determine if metric value is good based on target"""
        
        # Define tolerance ranges
        tolerances = {
            "llm_latency_ms": (0, 1.2),    # 20% tolerance
            "api_latency_ms": (0, 1.2),     # 20% tolerance
            "error_rate": (0, 1.5),        # 50% tolerance
            "success_rate": (0.95, 1.0),    # 5% tolerance
            "memory_usage_mb": (0, 1.2),     # 20% tolerance
            "cpu_usage_percent": (0, 1.2),   # 20% tolerance
            "avg_relevance_score": (0.9, 1.1),  # 10% tolerance
            "cuisine_diversity": (0.5, 1.0),    # 20% tolerance
            "constraint_satisfaction_rate": (0.85, 1.0) # 15% tolerance
        }
        
        min_allowed, max_allowed = tolerances.get(metric_name, (0, float('inf')))
        return min_allowed <= current_value <= max_allowed
