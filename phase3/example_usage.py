"""
Example Usage of Phase 3 LLM Orchestration

Demonstrates how to use the Phase 3 components for restaurant recommendation.
"""

import asyncio
import logging
from typing import List

from orchestrator import RecommendationOrchestrator, quick_recommend
from prompt_builder import UserPreferences, RestaurantCandidate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_preferences() -> UserPreferences:
    """Create sample user preferences"""
    return UserPreferences(
        location="New York",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0
    )


def create_sample_candidates() -> List[RestaurantCandidate]:
    """Create sample restaurant candidates"""
    return [
        RestaurantCandidate(
            name="Tony's Italian Bistro",
            cuisines=["Italian", "Pizza"],
            rating=4.5,
            cost_for_two=60,
            location="Manhattan",
            votes=1250
        ),
        RestaurantCandidate(
            name="Luigi's Trattoria",
            cuisines=["Italian", "Mediterranean"],
            rating=4.2,
            cost_for_two=45,
            location="Brooklyn",
            votes=890
        ),
        RestaurantCandidate(
            name="Carlo's Kitchen",
            cuisines=["Italian", "Continental"],
            rating=4.7,
            cost_for_two=80,
            location="Queens",
            votes=2100
        ),
        RestaurantCandidate(
            name="Pasta Paradise",
            cuisines=["Italian", "Pasta"],
            rating=3.9,
            cost_for_two=35,
            location="Manhattan",
            votes=650
        )
    ]


async def example_basic_usage():
    """Example of basic orchestrator usage"""
    print("\n=== Basic Usage Example ===")
    
    # Create orchestrator with mock provider
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    
    # Get sample data
    preferences = create_sample_preferences()
    candidates = create_sample_candidates()
    
    # Generate recommendations
    response = await orchestrator.generate_recommendations(preferences, candidates)
    
    # Display results
    print(f"Summary: {response.summary}")
    print(f"Total recommendations: {len(response.rankings)}")
    
    for ranking in response.rankings:
        print(f"\nRank {ranking.rank}: {ranking.restaurant_name}")
        print(f"  Score: {ranking.relevance_score}/100")
        print(f"  Explanation: {ranking.explanation}")
        print(f"  Highlights: {', '.join(ranking.highlights)}")


async def example_ui_formatting():
    """Example of formatting for UI consumption"""
    print("\n=== UI Formatting Example ===")
    
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    preferences = create_sample_preferences()
    candidates = create_sample_candidates()
    
    # Get recommendations
    response = await orchestrator.generate_recommendations(preferences, candidates)
    
    # Format for UI
    ui_data = orchestrator.format_recommendations_for_ui(response)
    
    print("UI-ready data:")
    print(f"  Total results: {ui_data['total_results']}")
    print(f"  Summary: {ui_data['summary']}")
    
    for ranking in ui_data['rankings']:
        print(f"\n  {ranking['rank']}. {ranking['name']}")
        print(f"     Score: {ranking['score']}/100")
        print(f"     {ranking['explanation']}")


async def example_no_candidates():
    """Example when no candidates are available"""
    print("\n=== No Candidates Example ===")
    
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    preferences = create_sample_preferences()
    empty_candidates = []
    
    # Generate recommendations with no candidates
    response = await orchestrator.generate_recommendations(preferences, empty_candidates)
    
    print(f"Summary: {response.summary}")
    if response.suggestions:
        print("Suggestions:")
        for suggestion in response.suggestions:
            print(f"  - {suggestion}")


async def example_quick_recommend():
    """Example of quick convenience function"""
    print("\n=== Quick Recommend Example ===")
    
    preferences = create_sample_preferences()
    candidates = create_sample_candidates()
    
    # Quick recommendation
    response = await quick_recommend(preferences, candidates, provider="mock")
    
    print(f"Quick recommendation summary: {response.summary}")
    for ranking in response.rankings:
        print(f"  {ranking.rank}. {ranking.restaurant_name} (Score: {ranking.relevance_score})")


async def example_batch_processing():
    """Example of batch processing multiple requests"""
    print("\n=== Batch Processing Example ===")
    
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    
    # Create multiple preference/candidate pairs
    preference_candidates_pairs = [
        (
            UserPreferences("New York", "Low", "Chinese", 3.5),
            create_sample_candidates()
        ),
        (
            UserPreferences("San Francisco", "High", "Japanese", 4.5),
            create_sample_candidates()
        )
    ]
    
    # Process batch
    responses = await orchestrator.batch_generate_recommendations(preference_candidates_pairs)
    
    print(f"Processed {len(responses)} batch requests:")
    for i, response in enumerate(responses):
        print(f"  Request {i+1}: {len(response.rankings)} recommendations")


async def example_system_status():
    """Example of getting system status"""
    print("\n=== System Status Example ===")
    
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    status = orchestrator.get_system_status()
    
    print("System Status:")
    print(f"  LLM Provider: {status['llm_provider']}")
    print(f"  Max Retries: {status['max_retries']}")
    print(f"  Fallback Enabled: {status['fallback_enabled']}")
    print("  Components:")
    for component, state in status['components'].items():
        print(f"    {component}: {state}")


async def example_input_validation():
    """Example of input validation"""
    print("\n=== Input Validation Example ===")
    
    orchestrator = RecommendationOrchestrator(llm_provider="mock")
    
    # Test valid input
    valid_preferences = create_sample_preferences()
    valid_candidates = create_sample_candidates()
    
    is_valid, error = orchestrator.validate_input_data(valid_preferences, valid_candidates)
    print(f"Valid input: {is_valid}")
    
    # Test invalid input
    invalid_preferences = UserPreferences("", "Medium", "", 6.0)  # Invalid
    is_valid, error = orchestrator.validate_input_data(invalid_preferences, valid_candidates)
    print(f"Invalid input: {is_valid}, Error: {error}")


async def main():
    """Run all examples"""
    print("Phase 3 LLM Orchestration Examples")
    print("=" * 50)
    
    examples = [
        example_basic_usage,
        example_ui_formatting,
        example_no_candidates,
        example_quick_recommend,
        example_batch_processing,
        example_system_status,
        example_input_validation
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            logger.error(f"Example {example.__name__} failed: {e}")
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
