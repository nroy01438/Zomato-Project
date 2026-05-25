"""
Authentication and Authorization System

Provides JWT-based authentication, user management, role-based access control,
and security features for the production backend.
"""

import asyncio
import logging
import secrets
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import json

# Try to import JWT libraries
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("PyJWT not available, using simple token system")

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.warning("bcrypt not available, using simple hashing")


class UserRole(Enum):
    """User roles for authorization"""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(Enum):
    """System permissions"""
    READ_RECOMMENDATIONS = "read_recommendations"
    WRITE_RECOMMENDATIONS = "write_recommendations"
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    READ_ANALYTICS = "read_analytics"
    WRITE_ANALYTICS = "write_analytics"
    MANAGE_CACHE = "manage_cache"
    MANAGE_SYSTEM = "manage_system"


@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    refresh_token_expiration_days: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 60


@dataclass
class User:
    """User entity"""
    id: int
    username: str
    email: Optional[str]
    password_hash: str
    role: UserRole
    permissions: Set[Permission]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class AuthToken:
    """Authentication token"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: str = "read"


@dataclass
class LoginAttempt:
    """Login attempt tracking"""
    ip_address: str
    username: str
    timestamp: datetime
    success: bool
    user_agent: Optional[str] = None


class AuthManager:
    """Production-ready authentication and authorization manager"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # In-memory user store (in production, use database)
        self.users: Dict[str, User] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.login_attempts: List[LoginAttempt] = []
        
        # Role-permission mapping
        self.role_permissions = self._setup_role_permissions()
        
        # Initialize with default admin user
        self._initialize_default_user()
    
    def _setup_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Setup role-permission mapping"""
        
        return {
            UserRole.GUEST: {
                Permission.READ_RECOMMENDATIONS
            },
            UserRole.USER: {
                Permission.READ_RECOMMENDATIONS,
                Permission.WRITE_RECOMMENDATIONS
            },
            UserRole.PREMIUM: {
                Permission.READ_RECOMMENDATIONS,
                Permission.WRITE_RECOMMENDATIONS,
                Permission.READ_ANALYTICS
            },
            UserRole.ADMIN: {
                Permission.READ_RECOMMENDATIONS,
                Permission.WRITE_RECOMMENDATIONS,
                Permission.READ_USERS,
                Permission.READ_ANALYTICS,
                Permission.MANAGE_CACHE
            },
            UserRole.SUPER_ADMIN: {
                Permission.READ_RECOMMENDATIONS,
                Permission.WRITE_RECOMMENDATIONS,
                Permission.READ_USERS,
                Permission.WRITE_USERS,
                Permission.READ_ANALYTICS,
                Permission.WRITE_ANALYTICS,
                Permission.MANAGE_CACHE,
                Permission.MANAGE_SYSTEM
            }
        }
    
    def _initialize_default_user(self):
        """Initialize default admin user"""
        
        default_admin = User(
            id=1,
            username="admin",
            email="admin@restaurant-app.com",
            password_hash=self._hash_password("admin123"),
            role=UserRole.SUPER_ADMIN,
            permissions=self.role_permissions[UserRole.SUPER_ADMIN],
            is_active=True,
            created_at=datetime.now()
        )
        
        self.users["admin"] = default_admin
        self.logger.info("Default admin user created")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using available method"""
        
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # Fallback to simple hash (not as secure)
            salt = secrets.token_hex(16)
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            except:
                return False
        else:
            # Fallback verification
            try:
                salt = password_hash[:32]  # Extract salt (simplified)
                computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
                return hmac.compare_digest(computed_hash, password_hash)
            except:
                return False
    
    def _generate_jwt_token(self, user: User, token_type: str = "access") -> str:
        """Generate JWT token"""
        
        if JWT_AVAILABLE:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'permissions': [p.value for p in user.permissions],
                'token_type': token_type,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + (
                    timedelta(hours=self.config.jwt_expiration_hours) if token_type == "access"
                    else timedelta(days=self.config.refresh_token_expiration_days)
                )
            }
            
            return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
        else:
            # Fallback simple token
            token_data = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'token_type': token_type,
                'timestamp': int(time.time())
            }
            
            token_string = json.dumps(token_data, sort_keys=True)
            signature = hmac.new(
                self.config.jwt_secret.encode(),
                token_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return f"{token_string}.{signature}"
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        
        if JWT_AVAILABLE:
            try:
                payload = jwt.decode(
                    token,
                    self.config.jwt_secret,
                    algorithms=[self.config.jwt_algorithm]
                )
                return payload
            except jwt.ExpiredSignatureError:
                self.logger.warning("Token expired")
                return None
            except jwt.InvalidTokenError:
                self.logger.warning("Invalid token")
                return None
        else:
            # Fallback verification
            try:
                token_parts = token.split('.')
                if len(token_parts) != 2:
                    return None
                
                token_data, signature = token_parts
                expected_signature = hmac.new(
                    self.config.jwt_secret.encode(),
                    token_data.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, expected_signature):
                    return None
                
                payload = json.loads(token_data)
                
                # Check expiration
                token_time = payload.get('timestamp', 0)
                if time.time() - token_time > (self.config.jwt_expiration_hours * 3600):
                    return None
                
                return payload
                
            except Exception:
                return None
    
    def _track_login_attempt(self, username: str, ip_address: str, success: bool, 
                           user_agent: Optional[str] = None):
        """Track login attempt for security"""
        
        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            timestamp=datetime.now(),
            success=success,
            user_agent=user_agent
        )
        
        self.login_attempts.append(attempt)
        
        # Keep only last 1000 attempts
        if len(self.login_attempts) > 1000:
            self.login_attempts = self.login_attempts[-1000:]
        
        # Update user login attempts
        if username in self.users:
            user = self.users[username]
            if success:
                user.login_attempts = 0
                user.locked_until = None
                user.last_login = datetime.now()
            else:
                user.login_attempts += 1
                
                # Lock account if too many attempts
                if user.login_attempts >= self.config.max_login_attempts:
                    user.locked_until = datetime.now() + timedelta(
                        minutes=self.config.lockout_duration_minutes
                    )
                    self.logger.warning(f"Account {username} locked due to too many failed attempts")
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked"""
        
        user = self.users.get(username)
        if not user:
            return False
        
        if user.locked_until and user.locked_until > datetime.now():
            return True
        
        return False
    
    # User management
    async def create_user(self, username: str, password: str, email: Optional[str] = None,
                        role: UserRole = UserRole.USER) -> Optional[User]:
        """Create a new user"""
        
        # Validate input
        if len(password) < self.config.password_min_length:
            raise ValueError(f"Password must be at least {self.config.password_min_length} characters")
        
        if username in self.users:
            raise ValueError("Username already exists")
        
        if email and any(u.email == email for u in self.users.values()):
            raise ValueError("Email already exists")
        
        # Create user
        user = User(
            id=len(self.users) + 1,
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role,
            permissions=self.role_permissions[role],
            is_active=True,
            created_at=datetime.now()
        )
        
        self.users[username] = user
        self.logger.info(f"User {username} created with role {role.value}")
        
        return user
    
    async def authenticate_user(self, username: str, password: str, ip_address: str,
                              user_agent: Optional[str] = None) -> Optional[AuthToken]:
        """Authenticate user and return tokens"""
        
        # Check if account is locked
        if self._is_account_locked(username):
            self.logger.warning(f"Login attempt for locked account: {username}")
            return None
        
        # Get user
        user = self.users.get(username)
        if not user or not user.is_active:
            self._track_login_attempt(username, ip_address, False, user_agent)
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._track_login_attempt(username, ip_address, False, user_agent)
            return None
        
        # Successful authentication
        self._track_login_attempt(username, ip_address, True, user_agent)
        
        # Generate tokens
        access_token = self._generate_jwt_token(user, "access")
        refresh_token = self._generate_jwt_token(user, "refresh")
        
        # Store session
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            'user_id': user.id,
            'username': username,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'ip_address': ip_address
        }
        
        self.logger.info(f"User {username} authenticated successfully")
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.jwt_expiration_hours * 3600
        )
    
    async def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """Refresh access token using refresh token"""
        
        payload = self._verify_jwt_token(refresh_token)
        if not payload or payload.get('token_type') != 'refresh':
            return None
        
        username = payload.get('username')
        user = self.users.get(username)
        
        if not user or not user.is_active:
            return None
        
        # Generate new tokens
        access_token = self._generate_jwt_token(user, "access")
        new_refresh_token = self._generate_jwt_token(user, "refresh")
        
        return AuthToken(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.config.jwt_expiration_hours * 3600
        )
    
    async def logout(self, access_token: str) -> bool:
        """Logout user and invalidate session"""
        
        payload = self._verify_jwt_token(access_token)
        if not payload:
            return False
        
        username = payload.get('username')
        
        # Remove session (find by username)
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.get('username') == username:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        self.logger.info(f"User {username} logged out")
        return True
    
    def get_current_user(self, access_token: str) -> Optional[User]:
        """Get current user from access token"""
        
        payload = self._verify_jwt_token(access_token)
        if not payload:
            return None
        
        username = payload.get('username')
        return self.users.get(username)
    
    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        
        return permission in user.permissions
    
    def has_role(self, user: User, role: UserRole) -> bool:
        """Check if user has specific role"""
        
        return user.role == role or user.role == UserRole.SUPER_ADMIN
    
    # Authorization middleware
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract token from kwargs or request context
                token = kwargs.get('access_token')
                if not token:
                    raise PermissionError("Authentication required")
                
                user = self.get_current_user(token)
                if not user:
                    raise PermissionError("Invalid authentication")
                
                if not self.has_permission(user, permission):
                    raise PermissionError(f"Permission {permission.value} required")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_role(self, role: UserRole):
        """Decorator to require specific role"""
        
        def decorator(func):
            async def wrapper(*args, **kwargs):
                token = kwargs.get('access_token')
                if not token:
                    raise PermissionError("Authentication required")
                
                user = self.get_current_user(token)
                if not user:
                    raise PermissionError("Invalid authentication")
                
                if not self.has_role(user, role):
                    raise PermissionError(f"Role {role.value} required")
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    # User management
    async def update_user_role(self, username: str, new_role: UserRole, admin_token: str) -> bool:
        """Update user role (requires admin permission)"""
        
        admin_user = self.get_current_user(admin_token)
        if not admin_user or not self.has_permission(admin_user, Permission.WRITE_USERS):
            raise PermissionError("Admin permission required")
        
        user = self.users.get(username)
        if not user:
            return False
        
        user.role = new_role
        user.permissions = self.role_permissions[new_role]
        
        self.logger.info(f"User {username} role updated to {new_role.value}")
        return True
    
    async def deactivate_user(self, username: str, admin_token: str) -> bool:
        """Deactivate user (requires admin permission)"""
        
        admin_user = self.get_current_user(admin_token)
        if not admin_user or not self.has_permission(admin_user, Permission.WRITE_USERS):
            raise PermissionError("Admin permission required")
        
        user = self.users.get(username)
        if not user:
            return False
        
        user.is_active = False
        
        # Remove active sessions
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.get('username') == username:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        self.logger.info(f"User {username} deactivated")
        return True
    
    # Security monitoring
    def get_login_attempts(self, hours: int = 24, successful_only: bool = False) -> List[Dict[str, Any]]:
        """Get recent login attempts"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        attempts = []
        for attempt in self.login_attempts:
            if attempt.timestamp >= cutoff_time:
                if not successful_only or attempt.success:
                    attempts.append({
                        'username': attempt.username,
                        'ip_address': attempt.ip_address,
                        'timestamp': attempt.timestamp.isoformat(),
                        'success': attempt.success,
                        'user_agent': attempt.user_agent
                    })
        
        return attempts
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        
        sessions = []
        for session_id, session in self.active_sessions.items():
            sessions.append({
                'session_id': session_id,
                'user_id': session['user_id'],
                'username': session['username'],
                'created_at': session['created_at'].isoformat(),
                'last_activity': session['last_activity'].isoformat(),
                'ip_address': session['ip_address']
            })
        
        return sessions
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        
        cutoff_time = datetime.now() - timedelta(minutes=self.config.session_timeout_minutes)
        
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session['last_activity'] < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        
        # Recent login attempts
        recent_attempts = self.get_login_attempts(24)
        successful_logins = [a for a in recent_attempts if a['success']]
        failed_logins = [a for a in recent_attempts if not a['success']]
        
        # Locked accounts
        locked_accounts = len([u for u in self.users.values() if u.locked_until and u.locked_until > datetime.now()])
        
        # Active sessions
        active_sessions = len(self.active_sessions)
        
        return {
            'total_users': len(self.users),
            'active_users': len([u for u in self.users.values() if u.is_active]),
            'locked_accounts': locked_accounts,
            'active_sessions': active_sessions,
            'successful_logins_24h': len(successful_logins),
            'failed_logins_24h': len(failed_logins),
            'unique_ips_24h': len(set(a['ip_address'] for a in recent_attempts))
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform authentication system health check"""
        
        health_status = {
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Test user creation and authentication
            test_user = await self.create_user(
                "health_check_user",
                "test12345",
                "health@test.com",
                UserRole.USER
            )
            
            # Test authentication
            auth_result = await self.authenticate_user(
                "health_check_user",
                "test12345",
                "127.0.0.1"
            )
            
            health_status['checks']['user_creation'] = test_user is not None
            health_status['checks']['authentication'] = auth_result is not None
            
            # Test token verification
            if auth_result:
                user = self.get_current_user(auth_result.access_token)
                health_status['checks']['token_verification'] = user is not None
            
            # Cleanup test user
            if "health_check_user" in self.users:
                del self.users["health_check_user"]
            
            # Overall health
            health_status['healthy'] = all(health_status['checks'].values())
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
            self.logger.error(f"Auth health check failed: {e}")
        
        return health_status
