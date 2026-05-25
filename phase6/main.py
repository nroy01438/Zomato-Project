"""
Phase 6 Production Backend - Main Entry Point

Demonstrates the complete production backend infrastructure with all components
working together for the AI-Powered Restaurant Recommendation System.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

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


class ProductionBackend:
    """Complete production backend system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Initialize all components
        self.gateway = None
        self.db_manager = None
        self.cache_manager = None
        self.auth_manager = None
        self.rate_limiter = None
        self.load_balancer = None
        self.health_monitor = None
        self.error_handler = None
        
        # Configuration
        self.config = self._load_configuration()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        import logging
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('phase6_backend.log')
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults"""
        
        return {
            'database': {
                'db_type': os.getenv('DB_TYPE', 'sqlite'),
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'restaurant_recommendations'),
                'username': os.getenv('DB_USERNAME', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'pool_size': int(os.getenv('DB_POOL_SIZE', 10))
            },
            'cache': {
                'backend': os.getenv('CACHE_BACKEND', 'memory'),
                'host': os.getenv('CACHE_HOST', 'localhost'),
                'port': int(os.getenv('CACHE_PORT', 6379)),
                'password': os.getenv('CACHE_PASSWORD', ''),
                'default_ttl': int(os.getenv('CACHE_TTL', 300))
            },
            'auth': {
                'jwt_secret': os.getenv('JWT_SECRET', 'your-secret-key-change-in-production'),
                'jwt_expiration_hours': int(os.getenv('JWT_EXPIRATION', 24)),
                'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', 8))
            },
            'rate_limiting': {
                'global_requests': int(os.getenv('RATE_LIMIT_GLOBAL', 1000)),
                'global_window': int(os.getenv('RATE_LIMIT_WINDOW', 60)),
                'user_requests': int(os.getenv('RATE_LIMIT_USER', 100)),
                'distributed': os.getenv('RATE_LIMIT_DISTRIBUTED', 'true').lower() == 'true'
            },
            'load_balancer': {
                'algorithm': os.getenv('LB_ALGORITHM', 'health_aware'),
                'health_check_interval': int(os.getenv('LB_HEALTH_CHECK', 30)),
                'enable_sticky_sessions': os.getenv('LB_STICKY_SESSIONS', 'true').lower() == 'true'
            },
            'monitoring': {
                'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 30)),
                'enable_alerts': os.getenv('ENABLE_ALERTS', 'true').lower() == 'true'
            }
        }
    
    async def initialize(self):
        """Initialize all backend components"""
        
        self.logger.info("🚀 Initializing Phase 6 Production Backend")
        
        try:
            # 1. Initialize Database Manager
            await self._initialize_database()
            
            # 2. Initialize Cache Manager
            await self._initialize_cache()
            
            # 3. Initialize Authentication Manager
            await self._initialize_auth()
            
            # 4. Initialize Rate Limiter
            await self._initialize_rate_limiter()
            
            # 5. Initialize Load Balancer
            await self._initialize_load_balancer()
            
            # 6. Initialize Health Monitor
            await self._initialize_monitoring()
            
            # 7. Initialize Error Handler
            await self._initialize_error_handler()
            
            # 8. Initialize API Gateway
            await self._initialize_gateway()
            
            # 9. Setup integrations between components
            await self._setup_integrations()
            
            # 10. Warm up cache with sample data
            await self._warm_up_cache()
            
            self.logger.info("✅ Phase 6 Production Backend initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize backend: {e}")
            raise
    
    async def _initialize_database(self):
        """Initialize database manager"""
        
        self.logger.info("📊 Initializing Database Manager")
        
        config = DatabaseConfig(
            db_type=self.config['database']['db_type'],
            host=self.config['database']['host'],
            port=self.config['database']['port'],
            database=self.config['database']['database'],
            username=self.config['database']['username'],
            password=self.config['database']['password'],
            pool_size=self.config['database']['pool_size']
        )
        
        self.db_manager = DatabaseManager(config)
        self.logger.info(f"   Database: {config.db_type} at {config.host}:{config.port}")
    
    async def _initialize_cache(self):
        """Initialize cache manager"""
        
        self.logger.info("💾 Initializing Cache Manager")
        
        cache_backend = self.config['cache']['backend']
        if cache_backend == 'redis':
            from phase6.cache import CacheBackend
            backend = CacheBackend.REDIS
        elif cache_backend == 'memcached':
            from phase6.cache import CacheBackend
            backend = CacheBackend.MEMCACHED
        else:
            from phase6.cache import CacheBackend
            backend = CacheBackend.MEMORY
        
        config = CacheConfig(
            backend=backend,
            host=self.config['cache']['host'],
            port=self.config['cache']['port'],
            password=self.config['cache']['password'],
            default_ttl=self.config['cache']['default_ttl']
        )
        
        self.cache_manager = CacheManager(config)
        self.logger.info(f"   Cache: {backend.value} backend")
    
    async def _initialize_auth(self):
        """Initialize authentication manager"""
        
        self.logger.info("🔐 Initializing Authentication Manager")
        
        config = AuthConfig(
            jwt_secret=self.config['auth']['jwt_secret'],
            jwt_expiration_hours=self.config['auth']['jwt_expiration_hours'],
            password_min_length=self.config['auth']['password_min_length']
        )
        
        self.auth_manager = AuthManager(config)
        self.logger.info(f"   JWT expiration: {config.jwt_expiration_hours} hours")
    
    async def _initialize_rate_limiter(self):
        """Initialize rate limiter"""
        
        self.logger.info("🚦 Initializing Rate Limiter")
        
        self.rate_limiter = RateLimiter(self.cache_manager)
        
        # Configure rate limits
        from phase6.rate_limiter import RateLimitConfig, RateLimitAlgorithm
        
        # Global rate limit
        self.rate_limiter.set_rate_limit_config('global', RateLimitConfig(
            requests_per_window=self.config['rate_limiting']['global_requests'],
            window_seconds=self.config['rate_limiting']['global_window'],
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            distributed=self.config['rate_limiting']['distributed']
        ))
        
        # Per-user rate limit
        self.rate_limiter.set_rate_limit_config('per_user', RateLimitConfig(
            requests_per_window=self.config['rate_limiting']['user_requests'],
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            distributed=self.config['rate_limiting']['distributed']
        ))
        
        self.logger.info(f"   Global limit: {self.config['rate_limiting']['global_requests']}/min")
        self.logger.info(f"   User limit: {self.config['rate_limiting']['user_requests']}/min")
    
    async def _initialize_load_balancer(self):
        """Initialize load balancer"""
        
        self.logger.info("⚖️  Initializing Load Balancer")
        
        config = LoadBalancerConfig(
            algorithm=self._get_load_balance_algorithm(),
            health_check_interval=self.config['load_balancer']['health_check_interval'],
            enable_sticky_sessions=self.config['load_balancer']['enable_sticky_sessions']
        )
        
        self.load_balancer = LoadBalancer(config)
        
        # Add mock servers for demonstration
        self.load_balancer.add_server("server1", "127.0.0.1", 8081, weight=2)
        self.load_balancer.add_server("server2", "127.0.0.1", 8082, weight=1)
        self.load_balancer.add_server("server3", "127.0.0.1", 8083, weight=1)
        
        self.logger.info(f"   Algorithm: {config.algorithm.value}")
        self.logger.info(f"   Servers: {len(self.load_balancer.get_all_servers())}")
    
    def _get_load_balance_algorithm(self):
        """Get load balancing algorithm from config"""
        
        from phase6.load_balancer import LoadBalanceAlgorithm
        
        algorithm_map = {
            'round_robin': LoadBalanceAlgorithm.ROUND_ROBIN,
            'least_connections': LoadBalanceAlgorithm.LEAST_CONNECTIONS,
            'weighted_round_robin': LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN,
            'ip_hash': LoadBalanceAlgorithm.IP_HASH,
            'random': LoadBalanceAlgorithm.RANDOM,
            'health_aware': LoadBalanceAlgorithm.HEALTH_AWARE
        }
        
        return algorithm_map.get(self.config['load_balancer']['algorithm'], LoadBalanceAlgorithm.HEALTH_AWARE)
    
    async def _initialize_monitoring(self):
        """Initialize health monitor"""
        
        self.logger.info("📈 Initializing Health Monitor")
        
        self.health_monitor = HealthMonitor("production_backend")
        
        # Add alert callbacks
        from phase6.monitoring import LoggingAlertCallback
        self.health_monitor.add_alert_callback(LoggingAlertCallback())
        
        self.logger.info(f"   Health check interval: {self.config['monitoring']['health_check_interval']}s")
    
    async def _initialize_error_handler(self):
        """Initialize error handler"""
        
        self.logger.info("🛡️  Initializing Error Handler")
        
        self.error_handler = ErrorHandler("production_backend")
        
        # Setup circuit breakers
        from phase6.error_handler import CircuitBreakerConfig
        self.error_handler.create_circuit_breaker(
            "database",
            CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30)
        )
        
        self.error_handler.create_circuit_breaker(
            "cache",
            CircuitBreakerConfig(failure_threshold=3, recovery_timeout=15)
        )
        
        self.error_handler.create_circuit_breaker(
            "external_api",
            CircuitBreakerConfig(failure_threshold=10, recovery_timeout=60)
        )
        
        # Setup retry policies
        self.error_handler.create_retry_policy(
            "database_operations",
            max_attempts=3,
            base_delay=1.0,
            backoff_multiplier=2.0
        )
        
        self.error_handler.create_retry_policy(
            "cache_operations",
            max_attempts=2,
            base_delay=0.5,
            backoff_multiplier=1.5
        )
        
        self.logger.info("   Circuit breakers: database, cache, external_api")
        self.logger.info("   Retry policies: database_operations, cache_operations")
    
    async def _initialize_gateway(self):
        """Initialize API Gateway"""
        
        self.logger.info("🌐 Initializing API Gateway")
        
        self.gateway = APIGateway()
        
        # Store references for middleware
        self.gateway.auth_manager = self.auth_manager
        self.gateway.rate_limiter = self.rate_limiter
        self.gateway.cache_manager = self.cache_manager
        self.gateway.error_handler = self.error_handler
        
        self.logger.info("   API Gateway ready with integrated components")
    
    async def _setup_integrations(self):
        """Setup integrations between components"""
        
        self.logger.info("🔗 Setting up component integrations")
        
        # Cache integration
        if self.cache_manager and self.db_manager:
            # Cache manager can use database for persistence
            pass
        
        # Monitoring integration
        if self.health_monitor:
            self.health_monitor.set_cache_manager(self.cache_manager)
            self.error_handler.set_health_monitor(self.health_monitor)
        
        # Error handling integration
        if self.error_handler:
            # Error handler can use monitoring for alerts
            pass
        
        self.logger.info("   Component integrations complete")
    
    async def _warm_up_cache(self):
        """Warm up cache with sample data"""
        
        self.logger.info("🔥 Warming up cache")
        
        # Sample restaurant data for cache warming
        sample_data = {
            "restaurants:location:New York": [
                {"name": "Tony's Italian Bistro", "rating": 4.5, "cuisine": "Italian"},
                {"name": "Sushi Master", "rating": 4.7, "cuisine": "Japanese"},
                {"name": "Burger Joint", "rating": 4.2, "cuisine": "American"}
            ],
            "restaurants:location:San Francisco": [
                {"name": "Golden Gate Grill", "rating": 4.6, "cuisine": "Californian"},
                {"name": "Fisherman's Wharf", "rating": 4.4, "cuisine": "Seafood"}
            ],
            "system:config": {
                "api_version": "6.0.0",
                "features": ["caching", "auth", "rate_limiting", "load_balancing"],
                "initialized_at": datetime.now().isoformat()
            }
        }
        
        await self.cache_manager.warm_cache(sample_data, ttl=3600)
        self.logger.info(f"   Cache warmed with {len(sample_data)} key sets")
    
    async def start(self):
        """Start the production backend"""
        
        self.logger.info("🚀 Starting Phase 6 Production Backend")
        
        try:
            # Start health monitoring
            self.health_monitor.start_monitoring()
            
            # Start auto-scaling if enabled
            from phase6.load_balancer import AutoScaler
            auto_scaler = AutoScaler(self.load_balancer, min_servers=2, max_servers=5)
            auto_scaler.start_auto_scaling()
            
            # Create Flask app
            app = self.gateway.create_flask_app()
            
            self.logger.info("✅ Production Backend started successfully")
            self.logger.info("📊 Health monitoring active")
            self.logger.info("⚖️  Load balancing active")
            self.logger.info("🌐 API Gateway ready")
            
            return app
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start backend: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the production backend"""
        
        self.logger.info("🛑 Shutting down Phase 6 Production Backend")
        
        try:
            # Stop monitoring
            if self.health_monitor:
                await self.health_monitor.stop_monitoring()
            
            # Close components
            if self.cache_manager:
                self.cache_manager.close()
            
            if self.db_manager:
                self.db_manager.close()
            
            if self.load_balancer:
                await self.load_balancer.close()
            
            if self.error_handler:
                self.error_handler.close()
            
            self.logger.info("✅ Production Backend shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'component': 'phase6_production_backend',
            'status': 'running',
            'components': {}
        }
        
        # Database status
        if self.db_manager:
            try:
                db_stats = self.db_manager.get_database_stats()
                status['components']['database'] = {
                    'status': 'healthy',
                    'stats': db_stats
                }
            except Exception as e:
                status['components']['database'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Cache status
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_metrics()
                status['components']['cache'] = {
                    'status': 'healthy',
                    'stats': cache_stats
                }
            except Exception as e:
                status['components']['cache'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Load balancer status
        if self.load_balancer:
            try:
                lb_stats = self.load_balancer.get_metrics()
                status['components']['load_balancer'] = {
                    'status': 'healthy',
                    'stats': lb_stats
                }
            except Exception as e:
                status['components']['load_balancer'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Health monitor status
        if self.health_monitor:
            try:
                health_status = self.health_monitor.get_overall_health()
                status['components']['health_monitor'] = {
                    'status': health_status['status'],
                    'summary': health_status['summary']
                }
            except Exception as e:
                status['components']['health_monitor'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Rate limiter status
        if self.rate_limiter:
            try:
                rate_limit_stats = self.rate_limiter.get_metrics()
                status['components']['rate_limiter'] = {
                    'status': 'healthy',
                    'stats': rate_limit_stats
                }
            except Exception as e:
                status['components']['rate_limiter'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Error handler status
        if self.error_handler:
            try:
                error_stats = self.error_handler.get_error_statistics()
                status['components']['error_handler'] = {
                    'status': 'healthy',
                    'stats': error_stats
                }
            except Exception as e:
                status['components']['error_handler'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return status


async def main():
    """Main entry point for Phase 6 Production Backend"""
    
    print("🚀 Phase 6 - Production Backend Architecture")
    print("=" * 60)
    print("Initializing enterprise-grade backend infrastructure...")
    print()
    
    backend = ProductionBackend()
    
    try:
        # Initialize all components
        await backend.initialize()
        
        print("\n📊 System Status:")
        status = backend.get_system_status()
        
        for component, info in status['components'].items():
            status_icon = "✅" if info['status'] == 'healthy' else "❌"
            print(f"   {status_icon} {component.title()}: {info['status']}")
        
        print(f"\n🌐 Starting API Gateway...")
        app = await backend.start()
        
        print(f"\n📡 API Gateway running on http://localhost:5000")
        print(f"📊 Health endpoint: http://localhost:5000/health")
        print(f"📋 API documentation: http://localhost:5000/")
        
        print(f"\n🎉 Phase 6 Production Backend is ready!")
        print("=" * 60)
        
        # Run the Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down gracefully...")
        await backend.shutdown()
        print("✅ Shutdown complete")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
