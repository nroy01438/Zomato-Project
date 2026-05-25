"""
Example Usage of Phase 4 Presentation Layer

Demonstrates how to use the Phase 4 components for restaurant recommendation
presentation including CLI, API, and web UI.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase4.main import Phase4Integration
from phase4.cli_interface import CLIInterface, CLIConfig
from phase4.api_endpoints import APIEndpoints, APIConfig
from phase4.ui_components import UIComponents, RenderConfig
from phase4.web_app import create_app

# Import from Phase 3
from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences, RestaurantCandidate


def create_sample_preferences():
    """Create sample user preferences for testing"""
    return UserPreferences(
        location="San Francisco",
        budget="Medium",
        cuisine="Japanese",
        min_rating=4.0
    )


def create_sample_candidates():
    """Create sample restaurant candidates"""
    return [
        RestaurantCandidate(
            name="Sushi Paradise",
            cuisines=["Japanese", "Sushi"],
            rating=4.7,
            cost_for_two=85,
            location="San Francisco",
            votes=1250
        ),
        RestaurantCandidate(
            name="Tokyo Dreams",
            cuisines=["Japanese", "Ramen"],
            rating=4.5,
            cost_for_two=60,
            location="San Francisco",
            votes=890
        ),
        RestaurantCandidate(
            name="Sakura Sushi",
            cuisines=["Japanese", "Sushi"],
            rating=4.3,
            cost_for_two=75,
            location="San Francisco",
            votes=650
        )
    ]


async def example_cli_interface():
    """Example of CLI interface usage"""
    print("\n" + "=" * 60)
    print("🖥️  CLI Interface Example")
    print("=" * 60)
    
    try:
        # Setup CLI with mock provider for demo
        config = CLIConfig(llm_provider="mock", show_debug=True)
        cli = CLIInterface(config)
        
        # Create sample data
        preferences = create_sample_preferences()
        candidates = create_sample_candidates()
        
        print(f"📝 Sample Preferences:")
        print(f"   Location: {preferences.location}")
        print(f"   Budget: {preferences.budget}")
        print(f"   Cuisine: {preferences.cuisine}")
        print(f"   Min Rating: {preferences.min_rating}")
        
        print(f"\n🔍 Found {len(candidates)} candidate restaurants")
        
        # Generate recommendations
        response = await cli.orchestrator.generate_recommendations(preferences, candidates)
        
        # Display results
        cli.display_recommendations(response)
        
    except Exception as e:
        print(f"❌ CLI Example Error: {e}")


async def example_ui_components():
    """Example of UI components usage"""
    print("\n" + "=" * 60)
    print("🎨 UI Components Example")
    print("=" * 60)
    
    try:
        # Setup orchestrator
        orchestrator = RecommendationOrchestrator(llm_provider="mock")
        preferences = create_sample_preferences()
        candidates = create_sample_candidates()
        
        # Generate recommendations
        response = await orchestrator.generate_recommendations(preferences, candidates)
        
        # Setup UI components
        ui_config = RenderConfig(theme="modern", show_scores=True, show_highlights=True)
        ui = UIComponents(ui_config)
        
        # Test different render formats
        print("📋 Card Layout:")
        cards = ui.render_cards(response)
        print(f"   Total Results: {cards['total_results']}")
        for card in cards['cards'][:2]:  # Show first 2
            print(f"   #{card['rank']} {card['restaurant_name']} (Score: {card.get('relevance_score', {}).get('display', 'N/A')})")
        
        print("\n📊 Table Layout:")
        table = ui.render_table(response)
        print(f"   Headers: {', '.join(table['headers'])}")
        print(f"   Rows: {len(table['rows'])}")
        
        print("\n📄 Compact Layout:")
        compact = ui.render_compact(response)
        print(f"   Items: {', '.join(compact['items'][:3])}...")
        
        print("\n🔍 Detailed Layout:")
        detailed = ui.render_detailed(response)
        for detail in detailed['details'][:2]:  # Show first 2
            metadata = detail['metadata']
            print(f"   #{detail['rank']} {detail['restaurant_name']}")
            print(f"     Score Category: {metadata.get('score_category', 'N/A')}")
        
        print("\n🌐 JSON API Format:")
        json_format = ui.render_json(response)
        print(f"   Success: {json_format['success']}")
        print(f"   Data Keys: {list(json_format['data'].keys())}")
        
    except Exception as e:
        print(f"❌ UI Components Example Error: {e}")


def example_api_endpoints():
    """Example of API endpoints setup"""
    print("\n" + "=" * 60)
    print("🔌 API Endpoints Example")
    print("=" * 60)
    
    try:
        # Setup API endpoints
        config = APIConfig(llm_provider="mock", host="127.0.0.1", port=5001)
        api = APIEndpoints(config)
        
        print("📡 Available Endpoints:")
        print("   GET  /           - API documentation")
        print("   GET  /health     - Health check")
        print("   POST /recommend  - Main recommendation endpoint")
        print("   POST /recommend/html - HTML recommendations")
        print("   POST /recommend/batch - Batch recommendations")
        print("   GET  /formats    - Available response formats")
        
        print(f"\n⚙️  API Configuration:")
        print(f"   Host: {config.host}")
        print(f"   Port: {config.port}")
        print(f"   LLM Provider: {config.llm_provider}")
        print(f"   CORS Enabled: {config.enable_cors}")
        
        # Test health check (would normally make HTTP request)
        print(f"\n💡 To test the API, run:")
        print(f"   python phase4/main.py --mode api --provider mock --port {config.port}")
        print(f"   Then visit: http://{config.host}:{config.port}/health")
        
    except Exception as e:
        print(f"❌ API Endpoints Example Error: {e}")


def example_web_app():
    """Example of web application setup"""
    print("\n" + "=" * 60)
    print("🌐 Web Application Example")
    print("=" * 60)
    
    try:
        # Setup web app
        config = APIConfig(llm_provider="mock", host="127.0.0.1", port=5002)
        app = create_app(config)
        
        print("🖥️  Web Application Features:")
        print("   ✅ Modern responsive UI with Tailwind CSS")
        print("   ✅ Interactive search form")
        print("   ✅ Real-time AI recommendations")
        print("   ✅ Card-based results display")
        print("   ✅ Loading states and error handling")
        print("   ✅ Mobile-friendly design")
        
        print(f"\n⚙️  Web App Configuration:")
        print(f"   Host: {config.host}")
        print(f"   Port: {config.port}")
        print(f"   LLM Provider: {config.llm_provider}")
        
        print(f"\n💡 To run the web app:")
        print(f"   python phase4/main.py --mode web --provider mock --port {config.port}")
        print(f"   Then visit: http://{config.host}:{config.port}/")
        
    except Exception as e:
        print(f"❌ Web App Example Error: {e}")


async def example_integration():
    """Example of full integration"""
    print("\n" + "=" * 60)
    print("🔗 Full Integration Example")
    print("=" * 60)
    
    try:
        # Setup integration
        integration = Phase4Integration(llm_provider="mock")
        
        # Get system status
        status = integration.get_system_status()
        print("📊 System Status:")
        print(f"   Phase: {status['phase']}")
        print(f"   LLM Provider: {status['llm_provider']}")
        
        print("\n🧩 Components:")
        for component, active in status['components'].items():
            icon = "✅" if active else "❌"
            print(f"   {icon} {component}")
        
        print("\n⭐ Features:")
        for feature, available in status['features'].items():
            icon = "✅" if available else "❌"
            print(f"   {icon} {feature}")
        
        # Test CLI setup
        print("\n🖥️  Testing CLI Setup...")
        cli = integration.setup_cli()
        print("   ✅ CLI interface initialized")
        
        # Test API setup
        print("\n🔌 Testing API Setup...")
        api = integration.setup_api()
        print("   ✅ API endpoints initialized")
        
        # Test Web App setup
        print("\n🌐 Testing Web App Setup...")
        app = integration.setup_web_app()
        print("   ✅ Web application initialized")
        
        print("\n💡 Integration Commands:")
        print("   python phase4/main.py --mode cli --provider mock")
        print("   python phase4/main.py --mode api --provider mock --port 5001")
        print("   python phase4/main.py --mode web --provider mock --port 5002")
        print("   python phase4/main.py --status")
        
    except Exception as e:
        print(f"❌ Integration Example Error: {e}")


async def example_api_testing():
    """Example of testing API endpoints"""
    print("\n" + "=" * 60)
    print("🧪 API Testing Example")
    print("=" * 60)
    
    try:
        import requests
        
        # Note: This would require the API server to be running
        print("📡 Sample API Test Commands:")
        print("\n# Health Check")
        print("curl -X GET http://localhost:5000/health")
        
        print("\n# Get Recommendations")
        print("curl -X POST http://localhost:5000/recommend \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print('    "location": "San Francisco",')
        print('    "budget": "Medium",')
        print('    "cuisine": "Japanese",')
        print('    "min_rating": 4.0')
        print("}'")
        
        print("\n# Get HTML Recommendations")
        print("curl -X POST http://localhost:5000/recommend/html \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print('    "location": "San Francisco",')
        print('    "budget": "Medium",')
        print('    "cuisine": "Japanese",')
        print('    "min_rating": 4.0,')
        print('    "format": "cards"')
        print("}'")
        
        print("\n# Batch Recommendations")
        print("curl -X POST http://localhost:5000/recommend/batch \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print('    "requests": [')
        print("      {")
        print('        "location": "San Francisco",')
        print('        "budget": "Medium",')
        print('        "cuisine": "Japanese",')
        print('        "min_rating": 4.0')
        print("      }")
        print("    ]")
        print("}'")
        
    except Exception as e:
        print(f"❌ API Testing Example Error: {e}")


async def main():
    """Run all examples"""
    print("Phase 4 Presentation Layer Examples")
    print("=" * 60)
    print("Demonstrating CLI, API, and Web UI capabilities")
    
    examples = [
        example_cli_interface,
        example_ui_components,
        example_api_endpoints,
        example_web_app,
        example_integration,
        example_api_testing
    ]
    
    for example in examples:
        try:
            if asyncio.iscoroutinefunction(example):
                await example()
            else:
                example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All Phase 4 examples completed!")
    print("\n📚 Quick Start Guide:")
    print("1. Set environment variables:")
    print("   export GROQ_API_KEY=your_groq_key")
    print("2. Run CLI mode:")
    print("   python phase4/main.py --mode cli --provider groq")
    print("3. Run Web mode:")
    print("   python phase4/main.py --mode web --provider groq")
    print("4. Run API mode:")
    print("   python phase4/main.py --mode api --provider groq")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
