"""
Phase 6 Production Backend - Example Usage and Demonstration

Demonstrates all Phase 6 components working together in a production environment.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Phase 6 components
from phase6.api_gateway import APIGateway
from phase6.database import DatabaseManager, DatabaseConfig
from phase6.cache import CacheManager, CacheConfig
from phase6.auth import AuthManager, AuthConfig, UserRole
from phase6.rate_limiter import RateLimiter, RateLimitConfig
from phase6.load_balancer import LoadBalancer, LoadBalancerConfig
from phase6.monitoring import HealthMonitor
from phase6.error_handler import ErrorHandler


async def demonstrate_api_gateway():
    """Demonstrate API Gateway functionality"""
    
    print("\n🌐 API Gateway Demo")
    print("-" * 40)
    
    gateway = APIGateway()
    
    # Test various endpoints
    endpoints = [
        ("GET", "/health"),
        ("GET", "/"),
        ("GET", "/formats"),
        ("POST", "/recommend", {
            "location": "New York",
            "budget": "Medium",
            "cuisine": "Italian",
            "min_rating": 4.0
        })
    ]
    
    for method, path, *body in endpoints:
        try:
            request_body = body[0] if body else None
            response = await gateway.handle_request(method, path, body=request_body)
            
            print(f"✅ {method} {path}")
            print(f"   Status: {response.get('status', 'N/A')}")
            if 'data' in response:
                print(f"   Data keys: {list(response['data'].keys())}")
            print()
            
        except Exception as e:
            print(f"❌ {method} {path}: {e}")
    
    # Show route information
    routes_info = gateway.get_routes_info()
    print(f"📋 Total routes registered: {len(routes_info)}")
    
    return gateway


async def demonstrate_database():
    """Demonstrate database functionality"""
    
    print("\n📊 Database Demo")
    print("-" * 40)
    
    # Test SQLite (development)
    print("🔹 Testing SQLite Database")
    sqlite_config = DatabaseConfig(db_type="sqlite", database="demo_db")
    sqlite_db = DatabaseManager(sqlite_config)
    
    # Add sample restaurants
    sample_restaurants = [
        {
            "name": "Demo Restaurant 1",
            "cuisines": ["Italian", "Pizza"],
            "rating": 4.5,
            "cost_for_two": 1200,
            "location": "Demo City",
            "votes": 500
        },
        {
            "name": "Demo Restaurant 2",
            "cuisines": ["Japanese", "Sushi"],
            "rating": 4.7,
            "cost_for_two": 1800,
            "location": "Demo City",
            "votes": 750
        }
    ]
    
    for restaurant in sample_restaurants:
        restaurant_id = sqlite_db.insert_restaurant(restaurant)
        print(f"✅ Added restaurant: {restaurant['name']} (ID: {restaurant_id})")
    
    # Search restaurants
    results = sqlite_db.search_restaurants(
        location="Demo City",
        min_rating=4.0,
        limit=10
    )
    
    print(f"🔍 Found {len(results)} restaurants")
    
    # Get database statistics
    stats = sqlite_db.get_database_stats()
    print(f"📈 Database stats: {json.dumps(stats, indent=2)}")
    
    sqlite_db.close()
    
    return sqlite_db


async def demonstrate_cache():
    """Demonstrate caching functionality"""
    
    print("\n💾 Cache Demo")
    print("-" * 40)
    
    # Test memory cache
    print("🔹 Testing Memory Cache")
    memory_config = CacheConfig(backend="memory")
    cache_manager = CacheManager(memory_config)
    
    # Test basic operations
    await cache_manager.set("test_key", {"message": "Hello, World!"}, ttl=60)
    cached_value = await cache_manager.get("test_key")
    
    print(f"✅ Cache set/get: {cached_value}")
    
    # Test cache warming
    warm_data = {
        "user:123": {"name": "John Doe", "preferences": {"cuisine": "Italian"}},
        "user:456": {"name": "Jane Smith", "preferences": {"cuisine": "Japanese"}},
        "config:system": {"version": "6.0", "features": ["auth", "cache"]}
    }
    
    await cache_manager.warm_cache(warm_data, ttl=300)
    print(f"✅ Cache warmed with {len(warm_data)} entries")
    
    # Test cache metrics
    metrics = cache_manager.get_metrics()
    print(f"📊 Cache metrics: {json.dumps(metrics, indent=2)}")
    
    # Test cache health
    health = await cache_manager.health_check()
    print(f"🏥 Cache health: {health['healthy']}")
    
    cache_manager.close()
    
    return cache_manager


async def demonstrate_authentication():
    """Demonstrate authentication functionality"""
    
    print("\n🔐 Authentication Demo")
    print("-" * 40)
    
    auth_config = AuthConfig()
    auth_manager = AuthManager(auth_config)
    
    # Create users
    users = [
        ("john_doe", "password123", "john@example.com", UserRole.USER),
        ("jane_admin", "admin123", "jane@example.com", UserRole.ADMIN),
        ("premium_user", "premium123", "premium@example.com", UserRole.PREMIUM)
    ]
    
    for username, password, email, role in users:
        try:
            user = await auth_manager.create_user(username, password, email, role)
            print(f"✅ Created user: {username} ({role.value})")
        except Exception as e:
            print(f"❌ Failed to create {username}: {e}")
    
    # Test authentication
    print("\n🔑 Testing Authentication:")
    auth_results = await auth_manager.authenticate_user("john_doe", "password123", "127.0.0.1")
    
    if auth_results:
        print(f"✅ Authentication successful")
        print(f"   Token: {auth_results.access_token[:50]}...")
        print(f"   Expires in: {auth_results.expires_in}s")
    else:
        print("❌ Authentication failed")
    
    # Test token verification
    if auth_results:
        user = auth_manager.get_current_user(auth_results.access_token)
        if user:
            print(f"✅ Token verification successful")
            print(f"   User: {user.username} ({user.role.value})")
        else:
            print("❌ Token verification failed")
    
    # Test authorization
    if auth_results:
        user = auth_manager.get_current_user(auth_results.access_token)
        if user:
            from phase6.auth import Permission
            can_read = auth_manager.has_permission(user, Permission.READ_RECOMMENDATIONS)
            can_manage = auth_manager.has_permission(user, Permission.MANAGE_SYSTEM)
            
            print(f"📋 Authorization check:")
            print(f"   Can read recommendations: {can_read}")
            print(f"   Can manage system: {can_manage}")
    
    # Get security stats
    stats = auth_manager.get_security_stats()
    print(f"📊 Security stats: {json.dumps(stats, indent=2)}")
    
    return auth_manager


async def demonstrate_rate_limiting():
    """Demonstrate rate limiting functionality"""
    
    print("\n🚦 Rate Limiting Demo")
    print("-" * 40)
    
    rate_limiter = RateLimiter()
    
    # Test different rate limits
    test_cases = [
        ("global", None),
        ("per_user", "user123"),
        ("per_ip", "192.168.1.100"),
        ("recommendations", "user123")
    ]
    
    for limit_type, identifier in test_cases:
        print(f"\n📊 Testing {limit_type} rate limit:")
        
        # Make multiple requests
        allowed_count = 0
        for i in range(10):
            result = await rate_limiter.check_rate_limit(limit_type, identifier=identifier)
            
            if result.allowed:
                allowed_count += 1
                print(f"   Request {i+1}: ✅ Allowed (remaining: {result.remaining_requests})")
            else:
                print(f"   Request {i+1}: ❌ Blocked (retry after: {result.retry_after}s)")
                break
        
        print(f"   Total allowed: {allowed_count}/10")
    
    # Get rate limiting metrics
    metrics = rate_limiter.get_metrics()
    print(f"\n📈 Rate limiting metrics: {json.dumps(metrics, indent=2)}")
    
    return rate_limiter


async def demonstrate_load_balancing():
    """Demonstrate load balancing functionality"""
    
    print("\n⚖️  Load Balancing Demo")
    print("-" * 40)
    
    config = LoadBalancerConfig()
    load_balancer = LoadBalancer(config)
    
    # Add servers
    servers = [
        ("server1", "127.0.0.1", 8081, 2),
        ("server2", "127.0.0.1", 8082, 1),
        ("server3", "127.0.0.1", 8083, 1)
    ]
    
    for server_id, host, port, weight in servers:
        server = load_balancer.add_server(server_id, host, port, weight)
        print(f"✅ Added server: {server_id} at {host}:{port} (weight: {weight})")
    
    # Test load balancing algorithms
    algorithms = [
        "round_robin",
        "least_connections", 
        "weighted_round_robin",
        "random"
    ]
    
    for algorithm in algorithms:
        print(f"\n🔄 Testing {algorithm} algorithm:")
        
        # Update algorithm
        from phase6.load_balancer import LoadBalanceAlgorithm
        algorithm_map = {
            "round_robin": LoadBalanceAlgorithm.ROUND_ROBIN,
            "least_connections": LoadBalanceAlgorithm.LEAST_CONNECTIONS,
            "weighted_round_robin": LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN,
            "random": LoadBalanceAlgorithm.RANDOM
        }
        
        # Simulate requests
        server_selections = {}
        for i in range(10):
            # Temporarily change algorithm for testing
            original_algorithm = load_balancer.config.algorithm
            load_balancer.config.algorithm = algorithm_map[algorithm]
            
            server = load_balancer.get_server()
            if server:
                server_selections[server.id] = server_selections.get(server.id, 0) + 1
        
        # Restore original algorithm
        load_balancer.config.algorithm = original_algorithm
        
        # Show distribution
        print(f"   Distribution: {dict(server_selections)}")
    
    # Test request routing
    print(f"\n🌐 Testing request routing:")
    
    test_requests = [
        {"action": "get_recommendations", "location": "NYC"},
        {"action": "get_user_profile", "user_id": "123"},
        {"action": "update_preferences", "user_id": "456"}
    ]
    
    for i, request_data in enumerate(test_requests):
        result = await load_balancer.route_request(
            request_data,
            session_id=f"session_{i}",
            client_ip="192.168.1.100"
        )
        
        if result['success']:
            print(f"   Request {i+1}: ✅ Routed to {result['server_address']}")
        else:
            print(f"   Request {i+1}: ❌ {result['error']}")
    
    # Get load balancer metrics
    metrics = load_balancer.get_metrics()
    print(f"\n📈 Load balancer metrics: {json.dumps(metrics, indent=2)}")
    
    await load_balancer.close()
    
    return load_balancer


async def demonstrate_monitoring():
    """Demonstrate monitoring functionality"""
    
    print("\n📈 Monitoring Demo")
    print("-" * 40)
    
    health_monitor = HealthMonitor("demo_system")
    
    # Run health checks
    print("🔍 Running health checks:")
    results = await health_monitor.run_all_health_checks()
    
    for name, result in results.items():
        status_icon = "✅" if result.status.value == "healthy" else "❌"
        print(f"   {status_icon} {name}: {result.status.value} ({result.message})")
    
    # Get overall health
    overall_health = health_monitor.get_overall_health()
    print(f"\n🏥 Overall health: {overall_health['status']}")
    print(f"   Message: {overall_health['message']}")
    print(f"   Checks: {overall_health['summary']}")
    
    # Get system metrics
    metrics = health_monitor.get_system_metrics(10)
    if metrics:
        print(f"\n📊 System metrics (last 10 data points):")
        for i, metric in enumerate(metrics[-3:]):  # Show last 3
            print(f"   {i+1}. CPU: {metric['cpu_percent']:.1f}%, "
                  f"Memory: {metric['memory_percent']:.1f}%, "
                  f"Disk: {metric['disk_usage_percent']:.1f}%")
    
    # Get alerts
    alerts = health_monitor.get_alerts(limit=5)
    if alerts:
        print(f"\n🚨 Recent alerts:")
        for alert in alerts:
            print(f"   {alert['severity'].upper()}: {alert['title']}")
    
    await health_monitor.stop_monitoring()
    
    return health_monitor


async def demonstrate_error_handling():
    """Demonstrate error handling functionality"""
    
    print("\n🛡️  Error Handling Demo")
    print("-" * 40)
    
    error_handler = ErrorHandler("demo_system")
    
    # Test error classification and handling
    test_errors = [
        (ConnectionError("Database connection failed"), "database", "connect"),
        (TimeoutError("Request timeout"), "network", "api_call"),
        (ValueError("Invalid input data"), "validation", "process_data"),
        (PermissionError("Access denied"), "authorization", "access_resource")
    ]
    
    for error, component, operation in test_errors:
        print(f"\n🔍 Testing error: {type(error).__name__}")
        
        # Track error
        error_event = error_handler.track_error(error, component, operation, {
            "user_id": "demo_user",
            "request_id": f"req_{hash(str(error)) % 10000}"
        })
        
        print(f"   Category: {error_event.category.value}")
        print(f"   Severity: {error_event.severity.value}")
        print(f"   Recovery actions: {error_event.recovery_actions}")
        
        # Attempt recovery
        recovery_result = await error_handler.handle_error(error, component, operation)
        
        if recovery_result['handled']:
            print(f"   ✅ Recovery: {recovery_result['recovery_action']}")
        else:
            print(f"   ❌ Recovery failed: {recovery_result['message']}")
    
    # Test circuit breaker
    print(f"\n🔌 Testing Circuit Breaker:")
    
    from phase6.error_handler import CircuitBreakerConfig
    circuit_breaker = error_handler.create_circuit_breaker(
        "demo_circuit",
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5)
    )
    
    # Simulate failures
    print("   Simulating failures...")
    for i in range(5):
        try:
            async def failing_function():
                raise Exception(f"Simulated failure {i+1}")
            
            await circuit_breaker.call(failing_function)
            print(f"   Attempt {i+1}: ✅ Success")
            
        except Exception as e:
            print(f"   Attempt {i+1}: ❌ {e}")
    
    # Show circuit breaker state
    state = circuit_breaker.get_state()
    print(f"   Circuit state: {state['state']}")
    print(f"   Failure count: {state['failure_count']}")
    
    # Get error statistics
    stats = error_handler.get_error_statistics()
    print(f"\n📊 Error statistics: {json.dumps(stats, indent=2)}")
    
    return error_handler


async def demonstrate_integration():
    """Demonstrate all components working together"""
    
    print("\n🔗 Integration Demo")
    print("-" * 40)
    
    # Initialize all components
    print("🚀 Initializing all components...")
    
    cache_manager = CacheManager(CacheConfig(backend="memory"))
    auth_manager = AuthManager(AuthConfig())
    rate_limiter = RateLimiter(cache_manager)
    health_monitor = HealthMonitor("integrated_system")
    error_handler = ErrorHandler("integrated_system")
    
    # Setup integrations
    health_monitor.set_cache_manager(cache_manager)
    error_handler.set_health_monitor(health_monitor)
    
    print("✅ Components initialized")
    
    # Simulate a complete request flow
    print("\n🌐 Simulating complete request flow:")
    
    # 1. Rate limiting
    rate_result = await rate_limiter.check_user_limit("demo_user")
    if not rate_result.allowed:
        print("❌ Rate limited")
        return
    
    print("✅ Rate limit check passed")
    
    # 2. Authentication
    try:
        auth_result = await auth_manager.authenticate_user("admin", "admin123", "127.0.0.1")
        if not auth_result:
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
        
        # 3. Cache lookup
        cache_key = "recommendations:demo_user:italian"
        cached_data = await cache_manager.get(cache_key)
        
        if cached_data:
            print("✅ Cache hit")
            recommendations = cached_data
        else:
            print("🔄 Cache miss, generating recommendations")
            
            # Simulate recommendation generation
            recommendations = {
                "restaurants": [
                    {"name": "Italian Bistro", "rating": 4.5},
                    {"name": "Pizza Place", "rating": 4.2}
                ]
            }
            
            # Cache the result
            await cache_manager.set(cache_key, recommendations, ttl=300)
            print("✅ Recommendations cached")
        
        # 4. Health monitoring
        health_status = health_monitor.get_overall_health()
        print(f"✅ System health: {health_status['status']}")
        
        # 5. Error handling (simulate success)
        try:
            # Simulate successful operation
            result = {"success": True, "data": recommendations}
            print("✅ Operation completed successfully")
            
        except Exception as e:
            handled = await error_handler.handle_error(e, "recommendation", "get_recommendations")
            print(f"🛡️ Error handled: {handled['handled']}")
        
        print("🎉 Complete flow executed successfully!")
        
    except Exception as e:
        print(f"❌ Flow failed: {e}")
    
    # Show integrated metrics
    print(f"\n📊 Integrated Metrics:")
    
    cache_metrics = cache_manager.get_metrics()
    print(f"   Cache hit rate: {cache_metrics.get('hit_rate', 0):.1%}")
    
    security_stats = auth_manager.get_security_stats()
    print(f"   Active users: {security_stats['active_users']}")
    
    rate_limit_metrics = rate_limiter.get_metrics()
    print(f"   Total requests: {rate_limit_metrics['total_requests']}")
    
    health_summary = health_monitor.get_overall_health()
    print(f"   System health: {health_summary['status']}")
    
    error_stats = error_handler.get_error_statistics()
    print(f"   Error rate: {error_stats.get('error_rate', 0):.1%}")
    
    # Cleanup
    cache_manager.close()
    await health_monitor.stop_monitoring()
    
    print("✅ Integration demo completed")


async def main():
    """Run all Phase 6 demonstrations"""
    
    print("🚀 Phase 6 - Production Backend Architecture Examples")
    print("=" * 80)
    print("Demonstrating enterprise-grade backend infrastructure")
    print("=" * 80)
    
    demonstrations = [
        ("API Gateway", demonstrate_api_gateway),
        ("Database", demonstrate_database),
        ("Cache", demonstrate_cache),
        ("Authentication", demonstrate_authentication),
        ("Rate Limiting", demonstrate_rate_limiting),
        ("Load Balancing", demonstrate_load_balancing),
        ("Monitoring", demonstrate_monitoring),
        ("Error Handling", demonstrate_error_handling),
        ("Integration", demonstrate_integration)
    ]
    
    for name, demo_func in demonstrations:
        try:
            print(f"\n{'='*20}")
            print(f"🎯 Running: {name}")
            print(f"{'='*20}")
            
            if asyncio.iscoroutinefunction(demo_func):
                await demo_func()
            else:
                demo_func()
                
            print(f"✅ {name} completed")
            
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 All Phase 6 examples completed!")
    print("=" * 80)
    
    print("\n📚 Phase 6 Components Summary:")
    print("   ✅ API Gateway - Request routing and middleware")
    print("   ✅ Database Manager - PostgreSQL/SQLite with pooling")
    print("   ✅ Cache Manager - Redis/Memcached with invalidation")
    print("   ✅ Authentication - JWT auth with RBAC")
    print("   ✅ Rate Limiter - Multi-algorithm with distributed support")
    print("   ✅ Load Balancer - Multiple algorithms with auto-scaling")
    print("   ✅ Health Monitor - Comprehensive monitoring and alerting")
    print("   ✅ Error Handler - Circuit breakers and recovery strategies")
    
    print("\n💡 Usage:")
    print("   python phase6/main.py - Run complete production backend")
    print("   python phase6/example_usage.py - Run examples")
    print("   python phase6/main.py --help - See available options")
    
    print("\n🚀 Phase 6 Ready for Production!")
    print("   Enterprise-grade backend with full observability")
    print("   Scalable, secure, and highly available")


if __name__ == "__main__":
    asyncio.run(main())
