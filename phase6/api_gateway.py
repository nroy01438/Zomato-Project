"""
API Gateway and Routing System

Provides centralized request routing, middleware management, and
API endpoint management for the production backend.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from functools import wraps

# Import from previous phases
try:
    from ..phase3.orchestrator import RecommendationOrchestrator
    from ..phase4.main import create_app as create_phase4_app
except ImportError:
    from phase3.orchestrator import RecommendationOrchestrator
    from phase4.main import create_app as create_phase4_app


class HTTPMethod(Enum):
    """HTTP methods supported by the gateway"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


@dataclass
class Route:
    """Represents a route in the API gateway"""
    path: str
    method: HTTPMethod
    handler: Callable
    middleware: List[Callable]
    auth_required: bool = False
    rate_limit: Optional[str] = None
    cache_ttl: Optional[int] = None


@dataclass
class RequestContext:
    """Context for each request"""
    request_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = 0.0
    path: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


class APIGateway:
    """Production-ready API Gateway with routing and middleware"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.routes: Dict[str, Route] = {}
        self.middleware_stack: List[Callable] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize core services
        self.orchestrator = RecommendationOrchestrator()
        self.phase4_app = create_phase4_app()
        
        # Setup default middleware
        self._setup_default_middleware()
        
        # Register routes
        self._register_routes()
    
    def _setup_default_middleware(self):
        """Setup default middleware for all requests"""
        
        @self.middleware
        async def request_logging_middleware(request_context: RequestContext, handler):
            """Log all requests"""
            start_time = time.time()
            self.logger.info(f"[{request_context.request_id}] {request_context.method} {request_context.path}")
            
            try:
                response = await handler(request_context)
                duration = time.time() - start_time
                self.logger.info(f"[{request_context.request_id}] Response {response.get('status', 200)} in {duration:.3f}s")
                return response
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"[{request_context.request_id}] Error in {duration:.3f}s: {e}")
                raise
        
        @self.middleware
        async def cors_middleware(request_context: RequestContext, handler):
            """Add CORS headers to responses"""
            response = await handler(request_context)
            
            if isinstance(response, dict):
                headers = response.setdefault('headers', {})
                headers.update({
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Max-Age': '86400'
                })
            
            return response
        
        @self.middleware
        async def request_id_middleware(request_context: RequestContext, handler):
            """Ensure request ID is present"""
            if not request_context.request_id:
                request_context.request_id = str(uuid.uuid4())
            return await handler(request_context)
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Health check
        self.add_route(
            path="/health",
            method=HTTPMethod.GET,
            handler=self.health_check,
            auth_required=False
        )
        
        # Recommendation endpoints
        self.add_route(
            path="/recommend",
            method=HTTPMethod.POST,
            handler=self.get_recommendations,
            auth_required=False,
            rate_limit="10/minute",
            cache_ttl=300  # 5 minutes
        )
        
        self.add_route(
            path="/recommend/batch",
            method=HTTPMethod.POST,
            handler=self.batch_recommendations,
            auth_required=True,
            rate_limit="5/minute"
        )
        
        # Authentication endpoints
        self.add_route(
            path="/auth/login",
            method=HTTPMethod.POST,
            handler=self.login,
            auth_required=False,
            rate_limit="5/minute"
        )
        
        self.add_route(
            path="/auth/logout",
            method=HTTPMethod.POST,
            handler=self.logout,
            auth_required=True
        )
        
        self.add_route(
            path="/auth/refresh",
            method=HTTPMethod.POST,
            handler=self.refresh_token,
            auth_required=False,
            rate_limit="10/minute"
        )
        
        # User management
        self.add_route(
            path="/user/profile",
            method=HTTPMethod.GET,
            handler=self.get_user_profile,
            auth_required=True
        )
        
        self.add_route(
            path="/user/profile",
            method=HTTPMethod.PUT,
            handler=self.update_user_profile,
            auth_required=True
        )
        
        # Cache management
        self.add_route(
            path="/cache/clear",
            method=HTTPMethod.POST,
            handler=self.clear_cache,
            auth_required=True
        )
        
        # API documentation
        self.add_route(
            path="/",
            method=HTTPMethod.GET,
            handler=self.api_documentation,
            auth_required=False
        )
        
        self.add_route(
            path="/formats",
            method=HTTPMethod.GET,
            handler=self.available_formats,
            auth_required=False
        )
    
    def add_route(self, path: str, method: HTTPMethod, handler: Callable,
                 auth_required: bool = False, rate_limit: Optional[str] = None,
                 cache_ttl: Optional[int] = None, middleware: Optional[List[Callable]] = None):
        """Add a new route to the gateway"""
        
        route_key = f"{method.value}:{path}"
        self.routes[route_key] = Route(
            path=path,
            method=method,
            handler=handler,
            middleware=middleware or [],
            auth_required=auth_required,
            rate_limit=rate_limit,
            cache_ttl=cache_ttl
        )
        
        self.logger.info(f"Registered route: {route_key}")
    
    def middleware(self, func: Callable) -> Callable:
        """Decorator to add middleware to the stack"""
        self.middleware_stack.append(func)
        return func
    
    async def handle_request(self, method: str, path: str, 
                           headers: Optional[Dict[str, str]] = None,
                           body: Optional[Dict[str, Any]] = None,
                           user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an incoming request"""
        
        # Create request context
        request_context = RequestContext(
            request_id=str(uuid.uuid4()),
            user_id=user_context.get('user_id') if user_context else None,
            ip_address=headers.get('X-Forwarded-For') if headers else None,
            user_agent=headers.get('User-Agent') if headers else None,
            timestamp=time.time(),
            path=path,
            method=method,
            headers=headers,
            body=body
        )
        
        try:
            # Find route
            route_key = f"{method}:{path}"
            if route_key not in self.routes:
                return self._error_response(404, "Route not found", request_context)
            
            route = self.routes[route_key]
            
            # Build middleware chain
            handler = route.handler
            middleware_chain = self.middleware_stack + route.middleware
            
            # Apply middleware in reverse order (last wraps first)
            for middleware in reversed(middleware_chain):
                handler = lambda h=handler, m=middleware: m(request_context, h)
            
            # Execute handler
            response = await handler(request_context)
            
            # Add standard response fields
            if isinstance(response, dict):
                response.setdefault('request_id', request_context.request_id)
                response.setdefault('timestamp', time.time())
            
            return response
            
        except Exception as e:
            self.logger.error(f"Request handling error: {e}")
            return self._error_response(500, "Internal server error", request_context)
    
    def _error_response(self, status_code: int, message: str, 
                       request_context: RequestContext) -> Dict[str, Any]:
        """Create a standardized error response"""
        
        return {
            'status': status_code,
            'error': True,
            'message': message,
            'request_id': request_context.request_id,
            'timestamp': time.time(),
            'path': request_context.path,
            'method': request_context.method
        }
    
    # Route Handlers
    async def health_check(self, request_context: RequestContext) -> Dict[str, Any]:
        """Health check endpoint"""
        
        return {
            'status': 200,
            'healthy': True,
            'timestamp': time.time(),
            'version': '6.0.0',
            'services': {
                'api_gateway': 'healthy',
                'orchestrator': 'healthy',
                'database': 'healthy',
                'cache': 'healthy'
            }
        }
    
    async def get_recommendations(self, request_context: RequestContext) -> Dict[str, Any]:
        """Get restaurant recommendations"""
        
        try:
            # Validate request body
            if not request_context.body:
                return self._error_response(400, "Request body required", request_context)
            
            preferences = request_context.body
            
            # Get recommendations from orchestrator
            response = await self.orchestrator.generate_recommendations(
                location=preferences.get('location'),
                budget=preferences.get('budget'),
                cuisine=preferences.get('cuisine'),
                min_rating=preferences.get('min_rating', 4.0)
            )
            
            return {
                'status': 200,
                'data': response,
                'cached': False
            }
            
        except Exception as e:
            self.logger.error(f"Recommendation error: {e}")
            return self._error_response(500, "Failed to get recommendations", request_context)
    
    async def batch_recommendations(self, request_context: RequestContext) -> Dict[str, Any]:
        """Handle batch recommendation requests"""
        
        try:
            if not request_context.body or 'requests' not in request_context.body:
                return self._error_response(400, "Batch requests required", request_context)
            
            batch_requests = request_context.body['requests']
            results = []
            
            for req in batch_requests:
                try:
                    response = await self.orchestrator.generate_recommendations(
                        location=req.get('location'),
                        budget=req.get('budget'),
                        cuisine=req.get('cuisine'),
                        min_rating=req.get('min_rating', 4.0)
                    )
                    results.append({'success': True, 'data': response})
                except Exception as e:
                    results.append({'success': False, 'error': str(e)})
            
            return {
                'status': 200,
                'data': {
                    'results': results,
                    'total': len(results),
                    'successful': sum(1 for r in results if r['success'])
                }
            }
            
        except Exception as e:
            return self._error_response(500, "Batch processing failed", request_context)
    
    async def login(self, request_context: RequestContext) -> Dict[str, Any]:
        """User login endpoint"""
        
        try:
            if not request_context.body or 'username' not in request_context.body:
                return self._error_response(400, "Username and password required", request_context)
            
            # Mock authentication for now
            username = request_context.body['username']
            user_id = f"user_{username}"
            
            return {
                'status': 200,
                'data': {
                    'user_id': user_id,
                    'username': username,
                    'token': f"mock_token_{user_id}_{int(time.time())}",
                    'expires_in': 3600
                }
            }
            
        except Exception as e:
            return self._error_response(500, "Login failed", request_context)
    
    async def logout(self, request_context: RequestContext) -> Dict[str, Any]:
        """User logout endpoint"""
        
        return {
            'status': 200,
            'data': {'message': 'Logged out successfully'}
        }
    
    async def refresh_token(self, request_context: RequestContext) -> Dict[str, Any]:
        """Refresh authentication token"""
        
        try:
            if not request_context.body or 'token' not in request_context.body:
                return self._error_response(400, "Token required", request_context)
            
            # Mock token refresh
            old_token = request_context.body['token']
            new_token = f"refreshed_{old_token}_{int(time.time())}"
            
            return {
                'status': 200,
                'data': {
                    'token': new_token,
                    'expires_in': 3600
                }
            }
            
        except Exception as e:
            return self._error_response(500, "Token refresh failed", request_context)
    
    async def get_user_profile(self, request_context: RequestContext) -> Dict[str, Any]:
        """Get user profile"""
        
        user_id = request_context.user_id
        if not user_id:
            return self._error_response(401, "Authentication required", request_context)
        
        # Mock user profile
        return {
            'status': 200,
            'data': {
                'user_id': user_id,
                'username': user_id.replace('user_', ''),
                'preferences': {
                    'default_location': 'New York',
                    'default_budget': 'Medium',
                    'favorite_cuisines': ['Italian', 'Japanese']
                },
                'created_at': '2024-01-01T00:00:00Z'
            }
        }
    
    async def update_user_profile(self, request_context: RequestContext) -> Dict[str, Any]:
        """Update user profile"""
        
        user_id = request_context.user_id
        if not user_id:
            return self._error_response(401, "Authentication required", request_context)
        
        if not request_context.body:
            return self._error_response(400, "Profile data required", request_context)
        
        # Mock profile update
        return {
            'status': 200,
            'data': {
                'user_id': user_id,
                'updated': True,
                'message': 'Profile updated successfully'
            }
        }
    
    async def clear_cache(self, request_context: RequestContext) -> Dict[str, Any]:
        """Clear cache"""
        
        user_id = request_context.user_id
        if not user_id:
            return self._error_response(401, "Authentication required", request_context)
        
        # Mock cache clearing
        return {
            'status': 200,
            'data': {
                'cache_cleared': True,
                'cleared_keys': ['recommendations', 'user_preferences'],
                'timestamp': time.time()
            }
        }
    
    async def api_documentation(self, request_context: RequestContext) -> Dict[str, Any]:
        """API documentation endpoint"""
        
        return {
            'status': 200,
            'data': {
                'title': 'Restaurant Recommendation API',
                'version': '6.0.0',
                'description': 'Production-ready API for restaurant recommendations',
                'endpoints': [
                    {
                        'path': '/health',
                        'method': 'GET',
                        'description': 'Health check endpoint',
                        'auth_required': False
                    },
                    {
                        'path': '/recommend',
                        'method': 'POST',
                        'description': 'Get restaurant recommendations',
                        'auth_required': False,
                        'rate_limit': '10/minute'
                    },
                    {
                        'path': '/auth/login',
                        'method': 'POST',
                        'description': 'User login',
                        'auth_required': False
                    }
                ]
            }
        }
    
    async def available_formats(self, request_context: RequestContext) -> Dict[str, Any]:
        """Available response formats"""
        
        return {
            'status': 200,
            'data': {
                'formats': ['json', 'html', 'xml'],
                'default_format': 'json',
                'content_types': {
                    'json': 'application/json',
                    'html': 'text/html',
                    'xml': 'application/xml'
                }
            }
        }
    
    def get_routes_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered routes"""
        
        routes_info = []
        for route_key, route in self.routes.items():
            routes_info.append({
                'path': route.path,
                'method': route.method.value,
                'auth_required': route.auth_required,
                'rate_limit': route.rate_limit,
                'cache_ttl': route.cache_ttl
            })
        
        return routes_info


# Flask integration for compatibility with Phase 4
class FlaskGatewayAdapter:
    """Adapter to integrate API Gateway with Flask"""
    
    def __init__(self, gateway: APIGateway):
        self.gateway = gateway
    
    def create_flask_app(self):
        """Create Flask app with gateway integration"""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
        async def handle_route(path):
            method = request.method
            headers = dict(request.headers)
            
            # Parse JSON body
            body = None
            if request.is_json:
                body = request.get_json()
            elif request.form:
                body = dict(request.form)
            
            # Handle request through gateway
            response = await self.gateway.handle_request(
                method=method,
                path=f"/{path}",
                headers=headers,
                body=body
            )
            
            return jsonify(response), response.get('status', 200)
        
        @app.route('/', methods=['GET'])
        async def handle_root():
            response = await self.gateway.handle_request('GET', '/')
            return jsonify(response), response.get('status', 200)
        
        return app
