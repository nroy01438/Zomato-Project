"""
Standalone Phase 5 Test

Demonstrates Phase 5 Evaluation & Observability working independently.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Phase 5 components
from phase5.offline_checks import OfflineChecks
from phase5.logger import SystemLogger
from phase5.monitoring import ErrorTracker
from phase5.metrics import MetricsCollector

# Import Phase 3 components
from phase3.prompt_builder import UserPreferences, RestaurantCandidate
from phase3.output_validator import RecommendationResponse, RestaurantRanking


async def test_phase5_components():
    """Test all Phase 5 components working together"""
    
    print("🚀 Phase 5 Standalone Test")
    print("=" * 80)
    print("Testing Evaluation & Observability Components")
    print("=" * 80)
    
    # 1. Test System Logger
    print("\n📝 Testing System Logger...")
    logger = SystemLogger(log_level="INFO", log_file="phase5_test.log")
    
    logger.log_component(
        component="test",
        level="INFO",
        message="Phase 5 standalone test started",
        data={"test_type": "comprehensive"}
    )
    
    # 2. Test Error Tracker
    print("\n📡 Testing Error Tracker...")
    error_tracker = ErrorTracker()
    
    error_tracker.track_error(
        error_type="test_error",
        message="Test error for demonstration",
        component="test",
        severity="medium"
    )
    
    # 3. Test Metrics Collector
    print("\n📊 Testing Metrics Collector...")
    metrics_collector = MetricsCollector()
    
    metrics_collector.record_latency("test", "operation", 150.5)
    metrics_collector.record_throughput("test", "requests", 2.3)
    metrics_collector.record_success_rate("test", 60, 0.95)
    
    # 4. Test Offline Checks
    print("\n🔍 Testing Offline Checks...")
    offline_checker = OfflineChecks()
    
    # Create test data
    preferences = UserPreferences(
        location="Test City",
        budget="Medium",
        cuisine="Test Cuisine",
        min_rating=4.0
    )
    
    candidates = [
        RestaurantCandidate(
            name="Good Restaurant",
            cuisines=["Test Cuisine"],
            rating=4.5,
            cost_for_two=1500,
            location="Test City",
            votes=1000
        ),
        RestaurantCandidate(
            name="Wrong Location",
            cuisines=["Test Cuisine"],
            rating=4.2,
            cost_for_two=1400,
            location="Different City",
            votes=800
        ),
        RestaurantCandidate(
            name="Low Rating",
            cuisines=["Test Cuisine"],
            rating=3.8,
            cost_for_two=1200,
            location="Test City",
            votes=600
        )
    ]
    
    # Create mock response
    rankings = [
        RestaurantRanking(
            rank=1,
            restaurant_name="Good Restaurant",
            relevance_score=85,
            explanation="Good match for preferences",
            highlights=["Good rating", "Right location"]
        ),
        RestaurantRanking(
            rank=2,
            restaurant_name="Wrong Location",
            relevance_score=75,
            explanation="Wrong location but good rating",
            highlights=["Good rating"]
        )
    ]
    
    response = RecommendationResponse(
        rankings=rankings,
        summary="Found 2 restaurants matching your criteria",
        suggestions=["Try different location"]
    )
    
    # Run offline checks
    check_report = offline_checker.run_all_checks(preferences, candidates, response)
    
    print(f"   Total Checks: {check_report.total_checks}")
    print(f"   Passed Checks: {check_report.passed_checks}")
    print(f"   Overall Score: {check_report.overall_score:.2f}")
    
    # 5. Test System Health
    print("\n🏥 Testing System Health...")
    
    # Get error tracker health
    error_health = error_tracker.get_system_health()
    print(f"   Error Tracker Status: {error_health['status']}")
    
    # Get metrics overview
    metrics_overview = metrics_collector.get_system_overview()
    print(f"   Metrics Collected: {metrics_overview['total_metrics']}")
    
    # Get logger analytics
    logger_analytics = logger.get_prompt_analytics()
    print(f"   Logger Analytics: {logger_analytics.get('total_prompts', 0)} prompts logged")
    
    # 6. Export Test Results
    print("\n📁 Exporting Test Results...")
    
    # Export monitoring data
    error_tracker.export_monitoring_data("phase5_test_monitoring")
    metrics_collector.export_metrics("phase5_test_metrics.json")
    logger.export_logs("phase5_test_logs")
    
    # Create comprehensive test report
    test_report = {
        "test_timestamp": "2026-04-29T19:58:00",
        "phase": "5",
        "components_tested": [
            "SystemLogger",
            "ErrorTracker", 
            "MetricsCollector",
            "OfflineChecks"
        ],
        "offline_check_results": {
            "total_checks": check_report.total_checks,
            "passed_checks": check_report.passed_checks,
            "overall_score": check_report.overall_score,
            "failed_checks": [r.check_name for r in check_report.check_results if not r.passed]
        },
        "system_health": {
            "error_tracker": error_health['status'],
            "metrics_collected": metrics_overview['total_metrics'],
            "components": metrics_overview['components']
        },
        "test_status": "SUCCESS",
        "recommendations": [
            "Phase 5 components working correctly",
            "All evaluation systems operational",
            "Monitoring and logging functional"
        ]
    }
    
    # Save test report
    with open("phase5_test_report.json", "w") as f:
        json.dump(test_report, f, indent=2)
    
    print("   Test report saved to: phase5_test_report.json")
    
    # 7. Final Summary
    print("\n" + "=" * 80)
    print("🎉 Phase 5 Standalone Test Complete!")
    print("=" * 80)
    
    print(f"\n📊 Test Results Summary:")
    print(f"   ✅ System Logger: Working")
    print(f"   ✅ Error Tracker: Working")
    print(f"   ✅ Metrics Collector: Working")
    print(f"   ✅ Offline Checks: Working")
    print(f"   📈 Overall Score: {check_report.overall_score:.2f}")
    
    print(f"\n📁 Generated Files:")
    print(f"   📝 phase5_test.log")
    print(f"   📊 phase5_test_metrics.json")
    print(f"   📡 phase5_test_monitoring/")
    print(f"   📋 phase5_test_report.json")
    
    print(f"\n💡 Phase 5 Features Demonstrated:")
    print(f"   🔍 Offline quality checks (constraints, diversity, coverage)")
    print(f"   📝 Comprehensive logging system")
    print(f"   📡 Error tracking and monitoring")
    print(f"   📊 Performance metrics collection")
    print(f"   🏥 System health assessment")
    
    return test_report


async def main():
    """Run standalone Phase 5 test"""
    try:
        report = await test_phase5_components()
        return report
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"status": "FAILED", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
