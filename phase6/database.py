"""
Database Integration and Optimization Layer

Provides production-ready database management with PostgreSQL/SQLite support,
connection pooling, query optimization, and migrations.
"""

import asyncio
import logging
import sqlite3
import psycopg2
from psycopg2 import pool, sql
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
import json
import time
from datetime import datetime

# Import from previous phases
try:
    from ..phase1.data_loader import RestaurantData
    from ..phase3.prompt_builder import RestaurantCandidate
except ImportError:
    from phase1.data_loader import RestaurantData
    from phase3.prompt_builder import RestaurantCandidate


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: str = "sqlite"  # "sqlite" or "postgresql"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "restaurant_recommendations"
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query: str
    execution_time: float
    rows_affected: int
    timestamp: datetime


class DatabaseManager:
    """Production-ready database manager with optimization"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection_pool = None
        self.query_metrics: List[QueryMetrics] = []
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and schema"""
        
        if self.config.db_type == "sqlite":
            self._initialize_sqlite()
        elif self.config.db_type == "postgresql":
            self._initialize_postgresql()
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
        
        # Create tables
        self._create_tables()
        
        # Load initial data if needed
        self._load_initial_data()
    
    def _initialize_sqlite(self):
        """Initialize SQLite database"""
        
        self.logger.info("Initializing SQLite database")
        
        # SQLite doesn't need connection pooling, but we'll manage connections
        self.sqlite_path = f"{self.config.database}.db"
        
        # Create connection
        conn = sqlite3.connect(self.sqlite_path)
        conn.close()
        
        self.logger.info(f"SQLite database created: {self.sqlite_path}")
    
    def _initialize_postgresql(self):
        """Initialize PostgreSQL database with connection pooling"""
        
        self.logger.info("Initializing PostgreSQL database")
        
        try:
            # Create connection pool
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                host=self.config.host,
                port=self.config.port or 5432,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password
            )
            
            # Test connection
            conn = self.connection_pool.getconn()
            conn.close()
            
            self.logger.info("PostgreSQL connection pool created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables"""
        
        if self.config.db_type == "sqlite":
            self._create_sqlite_tables()
        elif self.config.db_type == "postgresql":
            self._create_postgresql_tables()
    
    def _create_sqlite_tables(self):
        """Create SQLite tables"""
        
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            
            # Restaurants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cuisines TEXT,  -- JSON array
                    rating REAL,
                    cost_for_two INTEGER,
                    location TEXT,
                    votes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    preferences TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Recommendations cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    preferences TEXT,  -- JSON object
                    response TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # Query logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_type TEXT,
                    query_text TEXT,
                    execution_time REAL,
                    rows_affected INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants(location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_cuisines ON restaurants(cuisines)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON recommendation_cache(cache_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON recommendation_cache(expires_at)")
            
            conn.commit()
            self.logger.info("SQLite tables created successfully")
    
    def _create_postgresql_tables(self):
        """Create PostgreSQL tables with optimizations"""
        
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                
                # Restaurants table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        cuisines JSONB,
                        rating DECIMAL(3,2),
                        cost_for_two INTEGER,
                        location VARCHAR(255),
                        votes INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        preferences JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Recommendations cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recommendation_cache (
                        id SERIAL PRIMARY KEY,
                        cache_key VARCHAR(500) UNIQUE NOT NULL,
                        preferences JSONB,
                        response JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """)
                
                # Query logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_logs (
                        id SERIAL PRIMARY KEY,
                        query_type VARCHAR(100),
                        query_text TEXT,
                        execution_time REAL,
                        rows_affected INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants(location)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_cuisines ON restaurants USING GIN(cuisines)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON recommendation_cache(cache_key)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON recommendation_cache(expires_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                
                conn.commit()
                self.logger.info("PostgreSQL tables created successfully")
                
        finally:
            self.connection_pool.putconn(conn)
    
    def _load_initial_data(self):
        """Load initial restaurant data if database is empty"""
        
        try:
            # Check if restaurants table is empty
            count = self.execute_query("SELECT COUNT(*) as count FROM restaurants").fetchone()
            
            if count and count[0] == 0:
                self.logger.info("Loading initial restaurant data")
                
                # Load sample data
                sample_restaurants = [
                    {
                        'name': 'Tony\'s Italian Bistro',
                        'cuisines': ['Italian', 'Pizza'],
                        'rating': 4.5,
                        'cost_for_two': 60,
                        'location': 'New York',
                        'votes': 1250
                    },
                    {
                        'name': 'Sushi Master',
                        'cuisines': ['Japanese', 'Sushi'],
                        'rating': 4.7,
                        'cost_for_two': 90,
                        'location': 'San Francisco',
                        'votes': 890
                    },
                    {
                        'name': 'Burger Joint',
                        'cuisines': ['American', 'Burgers'],
                        'rating': 4.2,
                        'cost_for_two': 40,
                        'location': 'Seattle',
                        'votes': 2100
                    }
                ]
                
                for restaurant in sample_restaurants:
                    self.insert_restaurant(restaurant)
                
                self.logger.info(f"Loaded {len(sample_restaurants)} sample restaurants")
                
        except Exception as e:
            self.logger.error(f"Failed to load initial data: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        
        if self.config.db_type == "sqlite":
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            try:
                yield conn
            finally:
                conn.close()
                
        elif self.config.db_type == "postgresql":
            conn = self.connection_pool.getconn()
            try:
                yield conn
            finally:
                self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a database query with metrics tracking"""
        
        start_time = time.time()
        
        try:
            if self.config.db_type == "sqlite":
                conn = sqlite3.connect(self.sqlite_path)
                conn.row_factory = sqlite3.Row
                try:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    result = cursor.fetchall()
                    rows_affected = cursor.rowcount
                    
                    conn.commit()
                    
                finally:
                    conn.close()
                    
            elif self.config.db_type == "postgresql":
                conn = self.connection_pool.getconn()
                try:
                    with conn.cursor() as cursor:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        
                        if query.strip().upper().startswith('SELECT'):
                            result = cursor.fetchall()
                        else:
                            result = cursor.statusmessage
                            conn.commit()
                        
                        rows_affected = cursor.rowcount
                        
                finally:
                    self.connection_pool.putconn(conn)
            
            # Record metrics
            execution_time = time.time() - start_time
            self._record_query_metrics(query, execution_time, rows_affected)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def _record_query_metrics(self, query: str, execution_time: float, rows_affected: int):
        """Record query performance metrics"""
        
        metric = QueryMetrics(
            query=query,
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now()
        )
        
        self.query_metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
        
        # Log slow queries
        if execution_time > 1.0:  # Queries taking more than 1 second
            self.logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
    
    # Restaurant operations
    def insert_restaurant(self, restaurant_data: Dict[str, Any]) -> int:
        """Insert a new restaurant"""
        
        if self.config.db_type == "sqlite":
            query = """
                INSERT INTO restaurants (name, cuisines, rating, cost_for_two, location, votes)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                restaurant_data['name'],
                json.dumps(restaurant_data['cuisines']),
                restaurant_data['rating'],
                restaurant_data['cost_for_two'],
                restaurant_data['location'],
                restaurant_data.get('votes', 0)
            )
            
        elif self.config.db_type == "postgresql":
            query = """
                INSERT INTO restaurants (name, cuisines, rating, cost_for_two, location, votes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (
                restaurant_data['name'],
                json.dumps(restaurant_data['cuisines']),
                restaurant_data['rating'],
                restaurant_data['cost_for_two'],
                restaurant_data['location'],
                restaurant_data.get('votes', 0)
            )
        
        result = self.execute_query(query, params)
        
        if self.config.db_type == "postgresql":
            return result[0][0]  # Return ID
        else:
            return self.execute_query("SELECT last_insert_rowid()")[0][0]
    
    def get_restaurants_by_location(self, location: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get restaurants by location"""
        
        query = "SELECT * FROM restaurants WHERE location = ?"
        params = (location,)
        
        if limit:
            query += " LIMIT ?"
            params = (location, limit)
        
        results = self.execute_query(query, params)
        
        # Convert to RestaurantCandidate objects
        restaurants = []
        for row in results:
            restaurant = dict(row)
            restaurant['cuisines'] = json.loads(restaurant['cuisines'])
            restaurants.append(RestaurantCandidate(**restaurant))
        
        return restaurants
    
    def search_restaurants(self, location: Optional[str] = None, 
                          cuisine: Optional[str] = None,
                          min_rating: Optional[float] = None,
                          max_cost: Optional[int] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Search restaurants with filters"""
        
        conditions = []
        params = []
        
        if location:
            conditions.append("location = ?")
            params.append(location)
        
        if cuisine:
            if self.config.db_type == "sqlite":
                conditions.append("cuisines LIKE ?")
                params.append(f'%{cuisine}%')
            else:
                conditions.append("cuisines ? ?")
                params.append(cuisine)
        
        if min_rating:
            conditions.append("rating >= ?")
            params.append(min_rating)
        
        if max_cost:
            conditions.append("cost_for_two <= ?")
            params.append(max_cost)
        
        query = "SELECT * FROM restaurants"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY rating DESC, votes DESC LIMIT ?"
        params.append(limit)
        
        results = self.execute_query(query, tuple(params))
        
        # Convert to RestaurantCandidate objects
        restaurants = []
        for row in results:
            restaurant = dict(row)
            restaurant['cuisines'] = json.loads(restaurant['cuisines'])
            restaurants.append(RestaurantCandidate(**restaurant))
        
        return restaurants
    
    # User operations
    def create_user(self, username: str, email: Optional[str] = None, 
                   preferences: Optional[Dict[str, Any]] = None) -> int:
        """Create a new user"""
        
        query = """
            INSERT INTO users (username, email, preferences)
            VALUES (?, ?, ?)
        """ if self.config.db_type == "sqlite" else """
            INSERT INTO users (username, email, preferences)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        
        params = (username, email, json.dumps(preferences) if preferences else None)
        
        result = self.execute_query(query, params)
        
        if self.config.db_type == "postgresql":
            return result[0][0]
        else:
            return self.execute_query("SELECT last_insert_rowid()")[0][0]
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        
        query = "SELECT * FROM users WHERE id = ?"
        result = self.execute_query(query, (user_id,))
        
        if result:
            user = dict(result[0])
            if user['preferences']:
                user['preferences'] = json.loads(user['preferences'])
            return user
        
        return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        
        query = """
            UPDATE users SET preferences = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """ if self.config.db_type == "sqlite" else """
            UPDATE users SET preferences = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        self.execute_query(query, (json.dumps(preferences), user_id))
        return True
    
    # Cache operations
    def cache_recommendation(self, cache_key: str, preferences: Dict[str, Any], 
                           response: Dict[str, Any], ttl_seconds: int = 300) -> bool:
        """Cache a recommendation response"""
        
        expires_at = datetime.now().timestamp() + ttl_seconds
        
        query = """
            INSERT OR REPLACE INTO recommendation_cache 
            (cache_key, preferences, response, expires_at)
            VALUES (?, ?, ?, ?)
        """ if self.config.db_type == "sqlite" else """
            INSERT INTO recommendation_cache 
            (cache_key, preferences, response, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cache_key) DO UPDATE SET
            preferences = EXCLUDED.preferences,
            response = EXCLUDED.response,
            expires_at = EXCLUDED.expires_at
        """
        
        params = (
            cache_key,
            json.dumps(preferences),
            json.dumps(response),
            expires_at
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache recommendation: {e}")
            return False
    
    def get_cached_recommendation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached recommendation"""
        
        query = """
            SELECT response FROM recommendation_cache 
            WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
        """ if self.config.db_type == "sqlite" else """
            SELECT response FROM recommendation_cache 
            WHERE cache_key = %s AND expires_at > CURRENT_TIMESTAMP
        """
        
        result = self.execute_query(query, (cache_key,))
        
        if result:
            return json.loads(result[0][0])
        
        return None
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        
        query = """
            DELETE FROM recommendation_cache WHERE expires_at <= CURRENT_TIMESTAMP
        """ if self.config.db_type == "sqlite" else """
            DELETE FROM recommendation_cache WHERE expires_at <= CURRENT_TIMESTAMP
        """
        
        self.execute_query(query)
        
        # Get count of deleted rows
        if self.config.db_type == "sqlite":
            return self.execute_query("SELECT changes()")[0][0]
        else:
            # For PostgreSQL, we'd need to get the count differently
            return 0
    
    # Performance optimization methods
    def get_query_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get query performance metrics"""
        
        recent_metrics = self.query_metrics[-limit:]
        
        return [
            {
                'query': metric.query[:100] + '...' if len(metric.query) > 100 else metric.query,
                'execution_time': metric.execution_time,
                'rows_affected': metric.rows_affected,
                'timestamp': metric.timestamp.isoformat()
            }
            for metric in recent_metrics
        ]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        stats = {}
        
        # Table row counts
        tables = ['restaurants', 'users', 'recommendation_cache', 'query_logs']
        for table in tables:
            try:
                count = self.execute_query(f"SELECT COUNT(*) FROM {table}").fetchone()
                stats[f"{table}_count"] = count[0] if count else 0
            except Exception as e:
                self.logger.warning(f"Could not get count for {table}: {e}")
                stats[f"{table}_count"] = 0
        
        # Cache hit ratio (simplified)
        try:
            total_cache = self.execute_query("SELECT COUNT(*) FROM recommendation_cache").fetchone()
            expired_cache = self.execute_query("SELECT COUNT(*) FROM recommendation_cache WHERE expires_at <= CURRENT_TIMESTAMP").fetchone()
            
            if total_cache and total_cache[0] > 0:
                stats['cache_hit_ratio'] = (total_cache[0] - (expired_cache[0] if expired_cache else 0)) / total_cache[0]
            else:
                stats['cache_hit_ratio'] = 0.0
                
        except Exception as e:
            stats['cache_hit_ratio'] = 0.0
        
        # Average query time
        if self.query_metrics:
            avg_time = sum(m.execution_time for m in self.query_metrics) / len(self.query_metrics)
            stats['avg_query_time'] = avg_time
            stats['slow_queries'] = len([m for m in self.query_metrics if m.execution_time > 1.0])
        else:
            stats['avg_query_time'] = 0.0
            stats['slow_queries'] = 0
        
        return stats
    
    def optimize_database(self):
        """Run database optimization routines"""
        
        self.logger.info("Running database optimization")
        
        if self.config.db_type == "sqlite":
            # Vacuum and analyze for SQLite
            self.execute_query("VACUUM")
            self.execute_query("ANALYZE")
            
        elif self.config.db_type == "postgresql":
            # Analyze for PostgreSQL
            self.execute_query("ANALYZE")
        
        # Clean up expired cache
        cleaned = self.cleanup_expired_cache()
        self.logger.info(f"Cleaned up {cleaned} expired cache entries")
        
        self.logger.info("Database optimization completed")
    
    def close(self):
        """Close database connections"""
        
        if self.config.db_type == "postgresql" and self.connection_pool:
            self.connection_pool.closeall()
            self.logger.info("PostgreSQL connection pool closed")
        
        self.logger.info("Database manager closed")
