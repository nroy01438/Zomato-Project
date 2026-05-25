"""
Test Phase 4 with Bellandur Example

Demonstrates the system with:
- Location: Bellandur
- Budget: 2000 (Medium)
- Rating: 4.0
- Target: Top 5 restaurants
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase4.cli_interface import CLIInterface, CLIConfig
from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences, RestaurantCandidate


def create_bellandur_candidates():
    """Create realistic restaurant candidates for Bellandur area"""
    return [
        RestaurantCandidate(
            name="Windmills Craftworks",
            cuisines=["American", "Brewery", "Continental"],
            rating=4.5,
            cost_for_two=1800,
            location="Bellandur",
            votes=3420
        ),
        RestaurantCandidate(
            name="Toit Brewpub",
            cuisines=["American", "Brewery", "Pub Food"],
            rating=4.4,
            cost_for_two=1600,
            location="Bellandur", 
            votes=2890
        ),
        RestaurantCandidate(
            name="The Black Pearl",
            cuisines=["Seafood", "Continental", "Asian"],
            rating=4.3,
            cost_for_two=2200,
            location="Bellandur",
            votes=1870
        ),
        RestaurantCandidate(
            name="Barbeque Nation",
            cuisines=["Barbecue", "North Indian", "Mughlai"],
            rating=4.2,
            cost_for_two=1400,
            location="Bellandur",
            votes=4560
        ),
        RestaurantCandidate(
            name="Absolute Barbecues",
            cuisines=["Barbecue", "Grill", "Continental"],
            rating=4.1,
            cost_for_two=1500,
            location="Bellandur",
            votes=3120
        ),
        RestaurantCandidate(
            name="Mainland China",
            cuisines=["Chinese", "Asian", "Thai"],
            rating=4.0,
            cost_for_two=1200,
            location="Bellandur",
            votes=2780
        ),
        RestaurantCandidate(
            name="Punjabi Rasoi",
            cuisines=["North Indian", "Punjabi", "Mughlai"],
            rating=3.9,
            cost_for_two=800,
            location="Bellandur",
            votes=1890
        ),
        RestaurantCandidate(
            name="Chai Point",
            cuisines=["Cafe", "Fast Food", "Beverages"],
            rating=3.8,
            cost_for_two=400,
            location="Bellandur",
            votes=980
        )
    ]


async def test_bellandur_recommendations():
    """Test Phase 4 with Bellandur location and specified criteria"""
    print("🍽️  Phase 4 Live Test - Bellandur Restaurant Recommendations")
    print("=" * 70)
    print("📍 Location: Bellandur")
    print("💰 Budget: 2000 (Medium range)")
    print("⭐ Minimum Rating: 4.0")
    print("🎯 Target: Top 5 restaurants")
    print("=" * 70)
    
    try:
        # Setup orchestrator with Groq provider (or mock for demo)
        orchestrator = RecommendationOrchestrator(llm_provider="groq")
        
        # Create user preferences for Bellandur
        preferences = UserPreferences(
            location="Bellandur",
            budget="Medium",  # Corresponds to ~2000 for two people
            cuisine="Any",     # Open to all cuisines
            min_rating=4.0
        )
        
        print("\n📝 User Preferences:")
        print(f"   📍 Location: {preferences.location}")
        print(f"   💰 Budget: {preferences.budget}")
        print(f"   🍜 Cuisine: {preferences.cuisine}")
        print(f"   ⭐ Min Rating: {preferences.min_rating}")
        
        # Create realistic candidates for Bellandur
        candidates = create_bellandur_candidates()
        
        # Filter candidates by minimum rating
        qualified_candidates = [c for c in candidates if c.rating >= preferences.min_rating]
        
        print(f"\n🔍 Found {len(qualified_candidates)} qualified restaurants in Bellandur")
        print(f"📊 Total candidates in database: {len(candidates)}")
        
        if qualified_candidates:
            print("\n📋 Qualified Restaurants:")
            for i, candidate in enumerate(qualified_candidates, 1):
                print(f"   {i}. {candidate.name} - {candidate.rating}⭐ - ₹{candidate.cost_for_two} for two")
        
        # Generate recommendations using LLM
        print(f"\n🤖 Generating AI recommendations using {orchestrator.llm_client.provider_name}...")
        response = await orchestrator.generate_recommendations(preferences, qualified_candidates)
        
        # Display results
        print("\n" + "=" * 70)
        print("🎯 AI Restaurant Recommendations for Bellandur")
        print("=" * 70)
        
        print(f"\n📊 Summary: {response.summary}")
        print(f"🍽️  Total Recommendations: {len(response.rankings)}")
        
        if response.rankings:
            print(f"\n🏆 Top {len(response.rankings)} Restaurant Recommendations:")
            print("-" * 70)
            
            for ranking in response.rankings:
                print(f"\n🥇 Rank #{ranking.rank}")
                print(f"🍽️  Restaurant: {ranking.restaurant_name}")
                print(f"⭐ Relevance Score: {ranking.relevance_score}/100")
                print(f"💭 Why we recommend: {ranking.explanation}")
                
                if ranking.highlights:
                    highlights_str = " • ".join(ranking.highlights)
                    print(f"✨ Highlights: {highlights_str}")
                
                # Find the original candidate for additional info
                original_candidate = next((c for c in qualified_candidates if c.name == ranking.restaurant_name), None)
                if original_candidate:
                    print(f"💰 Cost for Two: ₹{original_candidate.cost_for_two}")
                    print(f"📍 Location: {original_candidate.location}")
                    print(f"🗳️  Votes: {original_candidate.votes}")
                
                print("-" * 40)
        else:
            print("\n❌ No recommendations generated")
        
        # Show suggestions if available
        if response.suggestions:
            print(f"\n💡 Suggestions:")
            for suggestion in response.suggestions:
                print(f"   • {suggestion}")
        
        print(f"\n🎉 Enjoy your dining experience in Bellandur!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_with_mock_provider():
    """Test with mock provider for demonstration"""
    print("\n🧪 Testing with Mock Provider (for demo purposes)")
    print("=" * 70)
    
    try:
        # Setup with mock provider
        orchestrator = RecommendationOrchestrator(llm_provider="mock")
        
        preferences = UserPreferences(
            location="Bellandur",
            budget="Medium",
            cuisine="Any", 
            min_rating=4.0
        )
        
        candidates = create_bellandur_candidates()
        qualified_candidates = [c for c in candidates if c.rating >= preferences.min_rating]
        
        print(f"📝 Mock test with {len(qualified_candidates)} qualified restaurants")
        
        response = await orchestrator.generate_recommendations(preferences, qualified_candidates)
        
        print(f"\n📊 Mock Summary: {response.summary}")
        print(f"🍽️  Mock Recommendations: {len(response.rankings)}")
        
        for ranking in response.rankings:
            print(f"   {ranking.rank}. {ranking.restaurant_name} (Score: {ranking.relevance_score})")
        
    except Exception as e:
        print(f"❌ Mock test error: {e}")


async def main():
    """Run the Bellandur test"""
    print("🚀 Starting Phase 4 Live Test - Bellandur Example")
    
    # Test with mock provider first (always works)
    await test_with_mock_provider()
    
    # Try with Groq if available
    print("\n" + "=" * 70)
    print("🔧 Testing with Groq Provider (requires GROQ_API_KEY)")
    print("=" * 70)
    
    try:
        # Check if Groq is available
        import os
        if os.getenv("GROQ_API_KEY"):
            await test_bellandur_recommendations()
        else:
            print("⚠️  GROQ_API_KEY not set in environment")
            print("💡 To test with real Groq:")
            print("   export GROQ_API_KEY=your_groq_api_key")
            print("   python phase4/test_bellandur.py")
    except Exception as e:
        print(f"⚠️  Groq test failed: {e}")
        print("💡 This is expected if Groq package or API key is not available")
    
    print("\n" + "=" * 70)
    print("🎉 Phase 4 Bellandur Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
