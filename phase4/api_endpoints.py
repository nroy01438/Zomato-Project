"""
API Endpoints for Restaurant Recommendation System

Provides REST API endpoints including the /recommend endpoint.
"""

from flask import Flask, Blueprint, request, jsonify, render_template_string
from flask_cors import CORS
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import from Phase 3
try:
    from ..phase3.orchestrator import RecommendationOrchestrator
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase4.ui_components import UIComponents, RenderConfig
except ImportError:
    from phase3.orchestrator import RecommendationOrchestrator
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase4.ui_components import UIComponents, RenderConfig


@dataclass
class APIConfig:
    """Configuration for API endpoints"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    llm_provider: str = "groq"
    enable_cors: bool = True
    max_candidates: int = 10


class APIEndpoints:
    """API endpoints for restaurant recommendation system"""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self.app = Blueprint('api', __name__)
        self.orchestrator = None
        self.ui_components = UIComponents()
        
        # CORS will be applied to the main Flask app, not the blueprint
        
        self._setup_orchestrator()
        self._setup_routes()
        self._setup_error_handlers()
    
    def _setup_orchestrator(self):
        """Setup the recommendation orchestrator"""
        try:
            self.orchestrator = RecommendationOrchestrator(
                llm_provider=self.config.llm_provider,
                max_retries=3,
                enable_fallback=True
            )
        except Exception as e:
            logging.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/')
        def home():
            """Home page with API documentation"""
            return render_template_string(self._get_home_template())
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "service": "restaurant-recommendation-api",
                "version": "1.0.0",
                "llm_provider": self.config.llm_provider
            })
        
        @self.app.route('/recommend', methods=['POST'])
        async def recommend():
            """Main recommendation endpoint"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "No data provided"
                    }), 400
                
                # Validate required fields
                required_fields = ['location', 'budget', 'cuisine', 'min_rating']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            "success": False,
                            "error": f"Missing required field: {field}"
                        }), 400
                
                # Create user preferences
                preferences = UserPreferences(
                    location=data['location'],
                    budget=data['budget'],
                    cuisine=data['cuisine'],
                    min_rating=float(data['min_rating'])
                )
                
                # Validate preferences
                is_valid, error = self.orchestrator.validate_input_data(preferences, [])
                if not is_valid:
                    return jsonify({
                        "success": False,
                        "error": f"Invalid input: {error}"
                    }), 400
                
                # Create sample candidates (in real app, this comes from Phase 2)
                candidates = self._create_sample_candidates(preferences)
                
                if not candidates:
                    return jsonify({
                        "success": True,
                        "data": {
                            "summary": "No restaurants found matching your criteria",
                            "total_results": 0,
                            "rankings": [],
                            "suggestions": ["Try a different location", "Adjust your budget", "Consider other cuisine types"]
                        }
                    })
                
                # Generate recommendations
                response = await self.orchestrator.generate_recommendations(preferences, candidates)
                
                # Return formatted response
                return jsonify(self.ui_components.render_json(response))
                
            except Exception as e:
                logging.error(f"Error in recommend endpoint: {e}")
                return jsonify({
                    "success": False,
                    "error": "Internal server error"
                }), 500
        
        @self.app.route('/recommend/html', methods=['POST'])
        async def recommend_html():
            """Recommendation endpoint returning HTML"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"error": "No data provided"}), 400
                
                # Validate and create preferences
                preferences = UserPreferences(
                    location=data['location'],
                    budget=data['budget'],
                    cuisine=data['cuisine'],
                    min_rating=float(data['min_rating'])
                )
                
                candidates = self._create_sample_candidates(preferences)
                
                if not candidates:
                    return "<p>No restaurants found matching your criteria</p>"
                
                # Generate recommendations
                response = await self.orchestrator.generate_recommendations(preferences, candidates)
                
                # Render HTML
                render_format = data.get('format', 'cards')
                if render_format == 'table':
                    html = self.ui_components.render_html_table(response)
                else:
                    html = self.ui_components.render_html_cards(response)
                
                # Include CSS styles
                css = self.ui_components.get_css_styles()
                
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Restaurant Recommendations</title>
                    {css}
                </head>
                <body>
                    {html}
                </body>
                </html>
                """
                
            except Exception as e:
                logging.error(f"Error in recommend_html endpoint: {e}")
                return f"<p>Error: {str(e)}</p>", 500
        
        @self.app.route('/recommend/batch', methods=['POST'])
        async def recommend_batch():
            """Batch recommendation endpoint"""
            try:
                data = request.get_json()
                
                if not data or 'requests' not in data:
                    return jsonify({
                        "success": False,
                        "error": "Missing 'requests' field"
                    }), 400
                
                requests = data['requests']
                if not isinstance(requests, list):
                    return jsonify({
                        "success": False,
                        "error": "'requests' must be a list"
                    }), 400
                
                # Process batch
                preference_candidates_pairs = []
                for req_data in requests:
                    preferences = UserPreferences(
                        location=req_data['location'],
                        budget=req_data['budget'],
                        cuisine=req_data['cuisine'],
                        min_rating=float(req_data['min_rating'])
                    )
                    candidates = self._create_sample_candidates(preferences)
                    preference_candidates_pairs.append((preferences, candidates))
                
                # Generate batch recommendations
                responses = await self.orchestrator.batch_generate_recommendations(preference_candidates_pairs)
                
                # Format responses
                formatted_responses = []
                for response in responses:
                    formatted_responses.append(self.ui_components.render_json(response))
                
                return jsonify({
                    "success": True,
                    "data": {
                        "total_requests": len(requests),
                        "responses": formatted_responses
                    }
                })
                
            except Exception as e:
                logging.error(f"Error in recommend_batch endpoint: {e}")
                return jsonify({
                    "success": False,
                    "error": "Internal server error"
                }), 500
        
        @self.app.route('/formats')
        def get_formats():
            """Get available response formats"""
            return jsonify({
                "formats": {
                    "json": "Standard JSON response",
                    "html_cards": "HTML with card layout",
                    "html_table": "HTML with table layout",
                    "cards": "Card layout data",
                    "table": "Table layout data",
                    "compact": "Compact text format",
                    "detailed": "Detailed format with metadata"
                }
            })
    
    def _setup_error_handlers(self):
        """Setup error handlers"""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error": "Endpoint not found"
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": "Internal server error"
            }), 500
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                "success": False,
                "error": "Bad request"
            }), 400
    
    def _create_sample_candidates(self, preferences: UserPreferences) -> list[RestaurantCandidate]:
        """Create sample restaurant candidates"""
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
    
    def _get_home_template(self) -> str:
        """Get home page template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Restaurant Recommendation API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { color: #007bff; font-weight: bold; }
                .example { background: #fff; border: 1px solid #ddd; padding: 10px; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>🍽️ Restaurant Recommendation API</h1>
            <p>AI-powered restaurant recommendations with multiple LLM providers</p>
            
            <h2>Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /recommend</h3>
                <p>Main recommendation endpoint</p>
                <div class="example">
                    <strong>Request:</strong><br>
                    <code>{
  "location": "New York",
  "budget": "Medium", 
  "cuisine": "Italian",
  "min_rating": 4.0
}</code><br><br>
                    <strong>Response:</strong><br>
                    <code>{
  "success": true,
  "data": {
    "summary": "Found 2 restaurants matching your criteria",
    "total_results": 2,
    "rankings": [...],
    "suggestions": [...]
  }
}</code>
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /recommend/html</h3>
                <p>Get recommendations as HTML (cards or table)</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /recommend/batch</h3>
                <p>Process multiple recommendation requests</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /health</h3>
                <p>Health check endpoint</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /formats</h3>
                <p>Available response formats</p>
            </div>
            
            <h2>LLM Provider</h2>
            <p>Currently using: <strong>{{ llm_provider }}</strong></p>
        </body>
        </html>
        """.replace("{{ llm_provider }}", self.config.llm_provider)
    
    def run(self):
        """Run the Flask app"""
        self.app.run(
            host=self.config.host,
            port=self.config.port,
            debug=self.config.debug
        )


def create_app(config: Optional[APIConfig] = None) -> Flask:
    """Create Flask app for external use"""
    api = APIEndpoints(config)
    return api.app
