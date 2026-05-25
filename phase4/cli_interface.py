"""
CLI Interface for User Preferences

Provides command-line interface for collecting user preferences
and displaying restaurant recommendations.
"""

import asyncio
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import from Phase 3
try:
    from ..phase3.orchestrator import RecommendationOrchestrator
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
except ImportError:
    from phase3.orchestrator import RecommendationOrchestrator
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate


@dataclass
class CLIConfig:
    """Configuration for CLI interface"""
    llm_provider: str = "groq"
    max_candidates: int = 10
    show_debug: bool = False


class CLIInterface:
    """Command-line interface for restaurant recommendations"""
    
    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self.orchestrator = None
        self._setup_orchestrator()
    
    def _setup_orchestrator(self):
        """Setup the recommendation orchestrator"""
        try:
            self.orchestrator = RecommendationOrchestrator(
                llm_provider=self.config.llm_provider,
                max_retries=3,
                enable_fallback=True
            )
        except Exception as e:
            print(f"❌ Failed to initialize orchestrator: {e}")
            print("💡 Make sure your API keys are set in environment variables")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome message"""
        print("🍽️  AI Restaurant Recommendation System")
        print("=" * 50)
        print("Find your perfect dining experience with AI-powered recommendations!")
        print()
    
    def collect_user_preferences(self) -> UserPreferences:
        """Collect user preferences through interactive prompts"""
        print("📝 Please tell us about your preferences:")
        print()
        
        # Location
        location = self._get_input("📍 Location (city/area)", required=True)
        
        # Budget
        print("\n💰 Budget Options:")
        print("  1. Low (< $30 for two)")
        print("  2. Medium ($30-80 for two)") 
        print("  3. High (> $80 for two)")
        budget_choice = self._get_choice("💰 Select budget range", ["1", "2", "3"], required=True)
        budget_map = {"1": "Low", "2": "Medium", "3": "High"}
        budget = budget_map[budget_choice]
        
        # Cuisine
        cuisine = self._get_input("🍜 Preferred cuisine type", required=True)
        
        # Minimum rating
        print("\n⭐ Rating Options:")
        print("  1. Any rating")
        print("  2. 3.0+ stars")
        print("  3. 4.0+ stars") 
        print("  4. 4.5+ stars")
        rating_choice = self._get_choice("⭐ Minimum rating requirement", ["1", "2", "3", "4"], required=True)
        rating_map = {"1": 0.0, "2": 3.0, "3": 4.0, "4": 4.5}
        min_rating = rating_map[rating_choice]
        
        return UserPreferences(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating
        )
    
    def _get_input(self, prompt: str, required: bool = False) -> str:
        """Get user input with validation"""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if required and not value:
                    print("❌ This field is required. Please enter a value.")
                    continue
                return value
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
    
    def _get_choice(self, prompt: str, choices: list, required: bool = False) -> str:
        """Get user choice from provided options"""
        while True:
            try:
                value = input(f"{prompt} ({'/'.join(choices)}): ").strip()
                if required and not value:
                    print("❌ Please make a selection.")
                    continue
                if value in choices:
                    return value
                else:
                    print(f"❌ Invalid choice. Please select from: {', '.join(choices)}")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
    
    def create_sample_candidates(self, preferences: UserPreferences) -> list[RestaurantCandidate]:
        """Create sample restaurant candidates for demonstration"""
        # In a real implementation, this would come from Phase 2 retrieval layer
        sample_restaurants = [
            RestaurantCandidate(
                name="Bella Italia",
                cuisines=["Italian", "Pizza"],
                rating=4.5,
                cost_for_two=65,
                location=preferences.location,
                votes=1250
            ),
            RestaurantCandidate(
                name="Sushi Master",
                cuisines=["Japanese", "Sushi"],
                rating=4.7,
                cost_for_two=90,
                location=preferences.location,
                votes=890
            ),
            RestaurantCandidate(
                name="The Burger Joint",
                cuisines=["American", "Burgers"],
                rating=4.2,
                cost_for_two=40,
                location=preferences.location,
                votes=2100
            ),
            RestaurantCandidate(
                name="Spice Garden",
                cuisines=["Indian", "Asian"],
                rating=4.3,
                cost_for_two=55,
                location=preferences.location,
                votes=650
            ),
            RestaurantCandidate(
                name="Le Petit Bistro",
                cuisines=["French", "European"],
                rating=4.6,
                cost_for_two=85,
                location=preferences.location,
                votes=450
            )
        ]
        
        # Filter by minimum rating
        filtered = [r for r in sample_restaurants if r.rating >= preferences.min_rating]
        
        # Limit to max candidates
        return filtered[:self.config.max_candidates]
    
    def display_recommendations(self, response):
        """Display formatted recommendations"""
        print("\n" + "=" * 50)
        print("🎯 Restaurant Recommendations")
        print("=" * 50)
        
        print(f"\n📊 Summary: {response.summary}")
        
        if not response.rankings:
            print("\n❌ No restaurants found matching your criteria.")
            if response.suggestions:
                print("\n💡 Suggestions:")
                for suggestion in response.suggestions:
                    print(f"   • {suggestion}")
            return
        
        print(f"\n🍽️  Found {len(response.rankings)} recommendation(s):")
        print()
        
        for ranking in response.rankings:
            print(f"🥇 Rank #{ranking.rank}")
            print(f"📍 Restaurant: {ranking.restaurant_name}")
            print(f"⭐ Relevance Score: {ranking.relevance_score}/100")
            print(f"💭 Why we recommend it: {ranking.explanation}")
            
            if ranking.highlights:
                highlights_str = " • ".join(ranking.highlights)
                print(f"✨ Highlights: {highlights_str}")
            
            print("-" * 40)
        
        print("\n🎉 Enjoy your meal!")
    
    async def run_interactive(self):
        """Run interactive CLI session"""
        self.display_welcome()
        
        try:
            # Collect preferences
            preferences = self.collect_user_preferences()
            
            print(f"\n🔍 Searching for restaurants in {preferences.location}...")
            print("🤖 AI is analyzing your preferences...")
            
            # Create sample candidates (in real app, this comes from Phase 2)
            candidates = self.create_sample_candidates(preferences)
            
            if not candidates:
                print("\n❌ No restaurants found in our database for your criteria.")
                return
            
            # Generate recommendations
            response = await self.orchestrator.generate_recommendations(preferences, candidates)
            
            # Display results
            self.display_recommendations(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            if self.config.show_debug:
                import traceback
                traceback.print_exc()
    
    async def run_with_args(self, location: str, budget: str, cuisine: str, min_rating: float):
        """Run CLI with pre-provided arguments"""
        preferences = UserPreferences(
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating
        )
        
        candidates = self.create_sample_candidates(preferences)
        
        if not candidates:
            print("❌ No restaurants found for the given criteria")
            return
        
        print(f"🔍 Finding restaurants in {preferences.location}...")
        response = await self.orchestrator.generate_recommendations(preferences, candidates)
        self.display_recommendations(response)


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Restaurant Recommendation System")
    parser.add_argument("--location", help="Location/city")
    parser.add_argument("--budget", choices=["Low", "Medium", "High"], help="Budget range")
    parser.add_argument("--cuisine", help="Preferred cuisine")
    parser.add_argument("--rating", type=float, help="Minimum rating (0-5)")
    parser.add_argument("--provider", default="groq", choices=["groq", "openai", "anthropic", "mock"], 
                       help="LLM provider")
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    
    args = parser.parse_args()
    
    config = CLIConfig(
        llm_provider=args.provider,
        show_debug=args.debug
    )
    
    cli = CLIInterface(config)
    
    if all([args.location, args.budget, args.cuisine, args.rating is not None]):
        # Run with provided arguments
        asyncio.run(cli.run_with_args(args.location, args.budget, args.cuisine, args.rating))
    else:
        # Run interactively
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()
