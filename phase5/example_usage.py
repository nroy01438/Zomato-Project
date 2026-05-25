"""
Example Usage of Phase 5 Evaluation & Observability

Demonstrates how to use Phase 5 components for system evaluation,
monitoring, and observability.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase5.evaluator import RecommendationEvaluator
from phase5.logger import SystemLogger
from phase5.monitoring import ErrorTracker
from phase5.metrics import MetricsCollector


async def example_basic_evaluation():
    """Example of basic system evaluation"""
    print("\n" + "=" * 80)
    print("🧪 Phase 5 Basic Evaluation Example")
    print("=" * 80)
    
    # Setup evaluator with Groq provider
    evaluator = RecommendationEvaluator(llm_provider="groq")
    
    # Run comprehensive evaluation
    results = await evaluator.run_comprehensive_evaluation(
        save_results=True,
        output_dir="phase5_example_results"
    )
    
    print(f"\n📊 Overall Health: {results.get('overall_health', 'unknown').upper()}")
    print(f"📈 Pass Rate: {results.get('golden_tests', {}).get('pass_rate', 0):.1%}")
    print(f"📁 Results saved to: phase5_example_results/")


async def example_monitoring_demo():
    """Example of monitoring system usage"""
    print("\n" + "=" * 80)
    print("📡 Phase 5 Monitoring Demo")
    print("=" * 80)
    
    # Setup monitoring
    error_tracker = ErrorTracker()
    metrics_collector = MetricsCollector()
    
    # Simulate some system activity
    print("\n🔍 Simulating system activity...")
    
    # Track some metrics
    metrics_collector.record_latency("llm", "recommendation", 1850.5)
    metrics_collector.record_throughput("api", "recommend", 2.3)
    metrics_collector.record_memory_usage("orchestrator", 384.2)
    metrics_collector.record_cpu_usage("orchestrator", 45.8)
    
    # Track some errors
    error_tracker.track_error(
        error_type="validation_error",
        message="Invalid user preference format",
        component="api",
        severity="medium"
    )
    
    error_tracker.track_error(
        error_type="llm_timeout",
        message="LLM response timeout after 30 seconds",
        component="llm",
        severity="high"
    )
    
    # Get system health
    health = error_tracker.get_system_health()
    print(f"\n🏥 System Health: {health['status'].upper()}")
    print(f"📊 Error Summary: {health['error_summary']}")
    
    # Get performance summary
    perf_summary = metrics_collector.get_system_overview()
    print(f"\n📈 Performance Overview:")
    print(f"   Total Metrics: {perf_summary['total_metrics']}")
    print(f"   Components: {', '.join(perf_summary['components'])}")
    
    # Export monitoring data
    error_tracker.export_monitoring_data("phase5_monitoring_export")
    metrics_collector.export_metrics("phase5_metrics_export.json")
    
    print(f"\n📁 Monitoring data exported to phase5_monitoring_export/")


async def example_logging_demo():
    """Example of logging system usage"""
    print("\n" + "=" * 80)
    print("📝 Phase 5 Logging Demo")
    print("=" * 80)
    
    # Setup logger
    logger = SystemLogger(log_level="INFO", log_file="phase5_demo.log")
    
    # Log various system events
    logger.log_component(
        component="retrieval",
        level="INFO",
        message="Starting candidate filtering",
        data={"total_candidates": 15, "filters_applied": ["location", "rating", "cuisine"]}
    )
    
    logger.log_prompt(
        prompt_id="prompt_001",
        prompt_text="Find restaurants in New York with Italian cuisine and 4.0+ rating",
        prompt_version="v2.1",
        llm_provider="groq",
        model="llama-3.1-8b-instant",
        token_count=128,
        response_time_ms=1850,
        success=True,
        preferences={"location": "New York", "cuisine": "Italian", "min_rating": 4.0},
        candidates_count=8
    )
    
    logger.log_validation_result(
        validation_type="output_schema",
        input_data={"response_format": "json"},
        result=True,
        error_message=None
    )
    
    logger.log_api_request(
        method="POST",
        endpoint="/recommend",
        request_data={"location": "New York", "budget": "Medium"},
        response_status=200,
        response_time_ms=245,
        user_id="user_123"
    )
    
    logger.log_ui_interaction(
        action="recommendation_displayed",
        component="web",
        data={"recommendations_shown": 5, "user_interaction": "scroll_to_view_more"},
        user_id="user_123"
    )
    
    logger.log_performance_metrics(
        component="system",
        metrics={
            "total_requests": 1250,
            "avg_response_time": 220.5,
            "success_rate": 0.97
        }
    )
    
    print(f"\n📊 Prompt Analytics:")
    analytics = logger.get_prompt_analytics()
    print(f"   Total Prompts: {analytics['total_prompts']}")
    print(f"   Success Rate: {analytics['success_rate']:.1%}")
    print(f"   Avg Response Time: {analytics['avg_response_time_ms']:.1f}ms")
    
    print(f"\n📁 Logs saved to: phase5_demo.log")
    print(f"📁 Structured logs saved to: phase5_demo_structured.jsonl")


async def example_offline_checks():
    """Example of offline quality checks"""
    print("\n" + "=" * 80)
    print("🔍 Phase 5 Offline Checks Example")
    print("=" * 80)
    
    # Import required modules
    from phase5.offline_checks import OfflineChecks
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    
    # Setup offline checker
    checker = OfflineChecks()
    
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
        ),
        RestaurantCandidate(
            name="Different Cuisine",
            cuisines=["Other Cuisine"],
            rating=4.3,
            cost_for_two=1600,
            location="Test City",
            votes=900
        )
    ]
    
    # Run offline checks
    report = checker.run_all_checks(preferences, candidates, candidates)
    
    # Display results
    print(f"\n📊 Offline Check Results:")
    print(f"   Total Checks: {report.total_checks}")
    print(f"   Passed Checks: {report.passed_checks}")
    print(f"   Failed Checks: {report.failed_checks}")
    print(f"   Overall Score: {report.overall_score:.2f}")
    
    print(f"\n❌ Failed Checks:")
    for result in report.check_results:
        if not result.passed:
            print(f"   • {result.check_name}: {result.message}")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"   {i}. {rec}")
    
    print(f"\n📁 Check Details:")
    summary = checker.get_check_summary(report)
    for key, value in summary.items():
        print(f"   {key}: {value}")


async def example_golden_tests():
    """Example of golden test suite usage"""
    print("\n" + "=" * 80)
    print("🧪 Phase 5 Golden Tests Example")
    print("=" * 80)
    
    # Import required modules
    from phase5.golden_tests import GoldenTestSuite
    from phase3.orchestrator import RecommendationOrchestrator
    
    # Setup test suite and orchestrator
    test_suite = GoldenTestSuite()
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    
    # Run golden tests
    results = await test_suite.run_all_tests(orchestrator)
    
    # Display results
    print(f"\n📊 Golden Test Results:")
    print(f"   Total Tests: {results['total_tests']}")
    print(f"   Passed Tests: {results['passed_tests']}")
    print(f"   Failed Tests: {results['failed_tests']}")
    print(f"   Pass Rate: {results['pass_rate']:.1%}")
    
    print(f"\n❌ Failed Tests:")
    for test_result in results["test_results"]:
        if not test_result["passed"]:
            print(f"   • {test_result['name']}: {test_result['description']}")
    
    # Save test results
    test_suite.save_test_results(results, "phase5_golden_test_results.json")
    
    print(f"\n📁 Test results saved to: phase5_golden_test_results.json")


async def main():
    """Run all Phase 5 examples"""
    print("🚀 Phase 5 Evaluation & Observability Examples")
    print("Demonstrating comprehensive system evaluation and monitoring")
    
    examples = [
        ("Basic Evaluation", example_basic_evaluation),
        ("Monitoring Demo", example_monitoring_demo),
        ("Logging Demo", example_logging_demo),
        ("Offline Checks", example_offline_checks),
        ("Golden Tests", example_golden_tests)
    ]
    
    for name, example in examples:
        try:
            print(f"\n{'='*20}")
            print(f"🎯 Running: {name}")
            print(f"{'='*20}")
            
            if asyncio.iscoroutinefunction(example):
                await example()
            else:
                example()
                
            print(f"✅ {name} completed")
            
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 All Phase 5 examples completed!")
    print("=" * 80)
    
    print("\n📚 Phase 5 Components Summary:")
    print("   ✅ Offline Checks - Constraint satisfaction, diversity, coverage")
    print("   ✅ Golden Tests - Fixed inputs with expected outputs")
    print("   ✅ System Logger - Prompt/version logging, error tracking")
    print("   ✅ Error Tracker - Monitoring and alerting")
    print("   ✅ Metrics Collector - Performance metrics and baselines")
    print("   ✅ Evaluator - Comprehensive evaluation coordination")
    
    print("\n💡 Usage:")
    print("   python phase5/example_usage.py")
    print("   # Run individual examples")
    print("   # Run comprehensive evaluation:")
    print("   python phase5/evaluator.py")


if __name__ == "__main__":
    asyncio.run(main())
