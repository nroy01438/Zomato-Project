"""
Real Groq API Test for Bellandur Example

Loads API key from .env file and makes real LLM calls to Groq
for the Bellandur restaurant recommendation test.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences, RestaurantCandidate
from phase4.ui_components import UIComponents, RenderConfig


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
        )
    ]


async def test_real_groq_bellandur():
    """Test Phase 4 with real Groq API call for Bellandur"""
    print("🍽️  Phase 4 Real API Test - Bellandur with Groq")
    print("=" * 80)
    print("📍 Location: Bellandur")
    print("💰 Budget: ₹2000 for two people")
    print("⭐ Minimum Rating: 4.0")
    print("🎯 Target: Top 5 restaurants")
    print("🤖 LLM: Groq (real API call)")
    print("=" * 80)
    
    # Check if API key is available (try both variable names)
    groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not groq_api_key:
        print("❌ Groq API key not found in .env file")
        print("💡 Please add your Groq API key to .env file:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
        print("   or LLM_API_KEY=your_groq_api_key_here")
        return False
    
    print(f"✅ Found Groq API key: {groq_api_key[:10]}...{groq_api_key[-4:]}")
    
    try:
        # Create user preferences
        preferences = UserPreferences(
            location="Bellandur",
            budget="Medium",
            cuisine="Any",
            min_rating=4.0
        )
        
        print(f"\n📝 User Preferences:")
        print(f"   📍 Location: {preferences.location}")
        print(f"   💰 Budget: {preferences.budget} (~₹2000 for two)")
        print(f"   🍜 Cuisine: {preferences.cuisine}")
        print(f"   ⭐ Min Rating: {preferences.min_rating}")
        
        # Create candidates
        candidates = create_bellandur_candidates()
        qualified_candidates = [c for c in candidates if c.rating >= preferences.min_rating]
        
        print(f"\n🔍 Found {len(qualified_candidates)} qualified restaurants in Bellandur")
        print(f"📊 Total candidates in database: {len(candidates)}")
        
        print(f"\n📋 Qualified Restaurants (4.0+ rating):")
        for i, candidate in enumerate(qualified_candidates, 1):
            print(f"   {i}. {candidate.name}")
            print(f"      ⭐ {candidate.rating}/5.0 | 💰 ₹{candidate.cost_for_two} | 🗳️ {candidate.votes} votes")
            print(f"      🍜 {', '.join(candidate.cuisines)}")
        
        # Setup orchestrator with real Groq provider
        print(f"\n🤖 Initializing Groq LLM client...")
        orchestrator = RecommendationOrchestrator(llm_provider="groq")
        
        print(f"⚡ Making real API call to Groq...")
        print(f"🧠 Model: llama3-8b-8192 (fast inference)")
        print(f"📡 Processing preferences and candidates...")
        
        # Make real API call
        response = await orchestrator.generate_recommendations(preferences, qualified_candidates)
        
        # Display results
        print(f"\n" + "=" * 80)
        print(f"🎯 Real Groq AI Recommendations for Bellandur")
        print("=" * 80)
        
        print(f"\n📊 Summary: {response.summary}")
        print(f"🍽️  Total Recommendations: {len(response.rankings)}")
        
        if response.rankings:
            print(f"\n🏆 Top Restaurant Rankings:")
            print("-" * 80)
            
            for ranking in response.rankings:
                print(f"\n🥇 Rank #{ranking.rank}")
                print(f"🍽️  Restaurant: {ranking.restaurant_name}")
                print(f"⭐ Relevance Score: {ranking.relevance_score}/100")
                print(f"💭 AI Reasoning: {ranking.explanation}")
                
                if ranking.highlights:
                    highlights_str = " • ".join(ranking.highlights)
                    print(f"✨ Key Highlights: {highlights_str}")
                
                # Find the original candidate for additional info
                original_candidate = next((c for c in qualified_candidates if c.name == ranking.restaurant_name), None)
                if original_candidate:
                    print(f"💰 Cost for Two: ₹{original_candidate.cost_for_two}")
                    print(f"⭐ Actual Rating: {original_candidate.rating}/5.0")
                    print(f"🗳️  User Votes: {original_candidate.votes}")
                    print(f"📍 Location: {original_candidate.location}")
                    print(f"🍜 Cuisines: {', '.join(original_candidate.cuisines)}")
                
                print("-" * 60)
        else:
            print(f"\n❌ No recommendations generated")
        
        # Show suggestions if available
        if response.suggestions:
            print(f"\n💡 Suggestions:")
            for suggestion in response.suggestions:
                print(f"   • {suggestion}")
        
        print(f"\n🎉 Real Groq API call successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during real Groq API call: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_integration():
    """Test API integration with real Groq"""
    print(f"\n" + "=" * 80)
    print(f"🔌 API Integration Test")
    print("=" * 80)
    
    try:
        # Import and setup API endpoints
        from phase4.api_endpoints import APIEndpoints, APIConfig
        
        config = APIConfig(
            llm_provider="groq",
            host="127.0.0.1",
            port=5003,
            debug=False
        )
        
        api = APIEndpoints(config)
        
        print(f"✅ API endpoints configured with Groq provider")
        print(f"📡 Available endpoints:")
        print(f"   POST /recommend - Main recommendation endpoint")
        print(f"   POST /recommend/html - HTML recommendations")
        print(f"   GET /health - Health check")
        print(f"   GET /formats - Available formats")
        
        print(f"\n💡 To start API server:")
        print(f"   python phase4/main.py --mode api --provider groq --port 5003")
        
        print(f"\n🌐 To test API endpoint:")
        print(f"   curl -X POST http://localhost:5003/recommend \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"location\": \"Bellandur\", \"budget\": \"Medium\", \"cuisine\": \"Any\", \"min_rating\": 4.0}}'")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test error: {e}")
        return False


async def main():
    """Run the real Groq test"""
    print("🚀 Phase 4 Real Groq API Test")
    print("Testing with actual Groq API calls")
    
    # Test real Groq API
    success = await test_real_groq_bellandur()
    
    if success:
        # Test API integration
        await test_api_integration()
        
        print(f"\n" + "=" * 80)
        print(f"🎉 Real Groq Test Complete!")
        print(f"✅ Successfully made API calls to Groq")
        print(f"✅ Generated real AI recommendations")
        print(f"✅ Phase 4 working with live LLM")
        print("=" * 80)
    else:
        print(f"\n" + "=" * 80)
        print(f"⚠️  Real Groq Test Failed")
        print(f"💡 Please check your GROQ_API_KEY in .env file")
        print(f"💡 Make sure you have a valid Groq API key")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
