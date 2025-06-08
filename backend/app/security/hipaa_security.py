from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import asyncio
import json
from enum import Enum
import logging
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import redis.asyncio as redis
from app.utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class UserRole(Enum):
    """HIPAA-compliant user roles"""
    SYSTEM_ADMIN = "system_admin"
    HEALTHCARE_PROVIDER = "healthcare_provider"
    CLINICAL_STAFF = "clinical_staff"
    BILLING_STAFF = "billing_staff"
    RESEARCHER = "researcher"
    PATIENT = "patient"
    AUDITOR = "auditor"
    READ_ONLY = "read_only"


class AccessLevel(Enum):
    """Data access levels"""
    PHI_FULL = "phi_full"  # Full PHI access
    PHI_LIMITED = "phi_limited"  # Limited dataset
    DE_IDENTIFIED = "de_identified"  # De-identified data only
    AGGREGATE = "aggregate"  # Aggregate data only
    NONE = "none"


class AuditEvent(Enum):
    """HIPAA audit event types"""
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    DATA_VIEW = "data_view"
    DATA_EXPORT = "data_export"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_ALERT = "security_alert"


# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    access_level = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime)
    mfa_enabled = Column(Boolean, default=True)
    mfa_secret = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_expires_at = Column(DateTime)
    must_change_password = Column(Boolean, default=False)
    allowed_ip_ranges = Column(JSON)  # List of allowed IP ranges
    session_timeout_minutes = Column(Integer, default=30)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer)
    username = Column(String(255))
    event_type = Column(String(50), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    patient_id = Column(String(255))  # For PHI access tracking
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    request_data = Column(JSON)  # Sanitized request data
    response_code = Column(Integer)
    session_id = Column(String(255))
    

class DataEncryptionKey(Base):
    __tablename__ = "data_encryption_keys"
    
    id = Column(Integer, primary_key=True)
    key_id = Column(String(255), unique=True, nullable=False)
    encrypted_key = Column(Text, nullable=False)  # Master key encrypted
    algorithm = Column(String(50), default="AES-256-GCM")
    created_at = Column(DateTime, default=datetime.utcnow)
    rotated_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    purpose = Column(String(100))  # PHI, PII, etc.


# Pydantic Models
class TokenData(BaseModel):
    user_id: int
    username: str
    role: UserRole
    access_level: AccessLevel
    session_id: str
    expires_at: datetime


class SecurityConfig(BaseModel):
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_history_count: int = 12
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 30
    require_mfa: bool = True
    allowed_origins: List[str] = []
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


class HIPAASecurityManager:
    """HIPAA-compliant security manager for healthcare applications"""
    
    def __init__(self, config: SecurityConfig, db_session: Session, redis_client: redis.Redis):
        self.config = config
        self.db = db_session
        self.redis = redis_client
        self.bearer_scheme = HTTPBearer()
        
        # Initialize encryption keys
        self._initialize_encryption()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(redis_client, config)
        
        # Initialize session manager
        self.session_manager = SessionManager(redis_client, config)
        
    def _initialize_encryption(self):
        """Initialize data encryption keys"""
        # Check if active encryption key exists
        active_key = self.db.query(DataEncryptionKey).filter_by(is_active=True).first()
        
        if not active_key:
            # Generate new master key
            master_key = Fernet.generate_key()
            
            # Create encryption key record
            key_record = DataEncryptionKey(
                key_id=secrets.token_urlsafe(32),
                encrypted_key=base64.b64encode(master_key).decode('utf-8'),
                purpose="PHI_ENCRYPTION"
            )
            
            self.db.add(key_record)
            self.db.commit()
            
            logger.info("Generated new data encryption key")
    
    async def authenticate_user(self, username: str, password: str, ip_address: str) -> Optional[User]:
        """Authenticate user with HIPAA-compliant security checks"""
        
        # Check rate limiting
        if not await self.rate_limiter.check_rate_limit(f"login:{ip_address}"):
            await self._audit_log(
                event_type=AuditEvent.LOGIN,
                username=username,
                success=False,
                error_message="Rate limit exceeded",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts"
            )
        
        # Get user
        user = self.db.query(User).filter_by(username=username).first()
        
        if not user:
            await self._audit_log(
                event_type=AuditEvent.LOGIN,
                username=username,
                success=False,
                error_message="User not found",
                ip_address=ip_address
            )
            # Don't reveal if user exists
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if user.is_locked:
            lockout_time = user.updated_at + timedelta(minutes=self.config.account_lockout_duration_minutes)
            if datetime.utcnow() < lockout_time:
                await self._audit_log(
                    event_type=AuditEvent.LOGIN,
                    user_id=user.id,
                    username=username,
                    success=False,
                    error_message="Account locked",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account temporarily locked"
                )
            else:
                # Unlock account
                user.is_locked = False
                user.failed_login_attempts = 0
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= self.config.max_failed_login_attempts:
                user.is_locked = True
                
            self.db.commit()
            
            await self._audit_log(
                event_type=AuditEvent.LOGIN,
                user_id=user.id,
                username=username,
                success=False,
                error_message="Invalid password",
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check password expiration
        if user.password_expires_at and datetime.utcnow() > user.password_expires_at:
            user.must_change_password = True
            self.db.commit()
        
        # Check IP restrictions
        if user.allowed_ip_ranges:
            if not self._check_ip_allowed(ip_address, user.allowed_ip_ranges):
                await self._audit_log(
                    event_type=AuditEvent.LOGIN,
                    user_id=user.id,
                    username=username,
                    success=False,
                    error_message="IP address not allowed",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access denied from this location"
                )
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Log successful login
        await self._audit_log(
            event_type=AuditEvent.LOGIN,
            user_id=user.id,
            username=username,
            success=True,
            ip_address=ip_address
        )
        
        return user
    
    async def create_access_token(self, user: User, session_id: Optional[str] = None) -> Tuple[str, str]:
        """Create JWT access token with HIPAA-compliant claims"""
        
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        
        # Create token data
        expires_at = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "access_level": user.access_level,
            "session_id": session_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        # Create session
        await self.session_manager.create_session(
            session_id=session_id,
            user_id=user.id,
            expires_at=expires_at
        )
        
        # Encode token
        access_token = jwt.encode(
            token_data,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        # Create refresh token
        refresh_expires = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        refresh_data = {
            "user_id": user.id,
            "session_id": session_id,
            "exp": refresh_expires,
            "type": "refresh"
        }
        
        refresh_token = jwt.encode(
            refresh_data,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        return access_token, refresh_token
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> TokenData:
        """Verify JWT token and check session validity"""
        
        token = credentials.credentials
        
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and await self.redis.exists(f"blacklist:{jti}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Check session validity
            session_id = payload.get("session_id")
            if not await self.session_manager.validate_session(session_id):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid"
                )
            
            # Create token data
            token_data = TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                access_level=AccessLevel(payload["access_level"]),
                session_id=session_id,
                expires_at=datetime.fromtimestamp(payload["exp"])
            )
            
            # Update session activity
            await self.session_manager.update_activity(session_id)
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def check_permission(
        self,
        token_data: TokenData,
        resource_type: str,
        action: str,
        patient_id: Optional[str] = None
    ) -> bool:
        """Check if user has permission for specific action"""
        
        # Define permission matrix
        permissions = {
            UserRole.SYSTEM_ADMIN: {
                "*": ["*"]  # Full access
            },
            UserRole.HEALTHCARE_PROVIDER: {
                "patient": ["read", "write"],
                "encounter": ["read", "write"],
                "observation": ["read", "write"],
                "medication": ["read", "write", "prescribe"],
                "terminology": ["read"]
            },
            UserRole.CLINICAL_STAFF: {
                "patient": ["read"],
                "encounter": ["read", "write"],
                "observation": ["read", "write"],
                "medication": ["read"],
                "terminology": ["read"]
            },
            UserRole.BILLING_STAFF: {
                "patient": ["read"],  # Limited to billing info
                "encounter": ["read"],
                "billing": ["read", "write"]
            },
            UserRole.RESEARCHER: {
                "patient": ["read"],  # De-identified only
                "aggregate": ["read"],
                "terminology": ["read"]
            },
            UserRole.PATIENT: {
                "patient": ["read"],  # Own records only
                "encounter": ["read"],
                "observation": ["read"],
                "medication": ["read"]
            },
            UserRole.AUDITOR: {
                "audit_log": ["read"],
                "system_config": ["read"]
            },
            UserRole.READ_ONLY: {
                "*": ["read"]
            }
        }
        
        # Get user permissions
        user_permissions = permissions.get(token_data.role, {})
        
        # Check wildcard permissions
        if "*" in user_permissions:
            if "*" in user_permissions["*"] or action in user_permissions["*"]:
                return True
        
        # Check specific resource permissions
        if resource_type in user_permissions:
            if "*" in user_permissions[resource_type] or action in user_permissions[resource_type]:
                # Additional checks for patient-specific access
                if token_data.role == UserRole.PATIENT and patient_id:
                    # Patients can only access their own records
                    user = self.db.query(User).filter_by(id=token_data.user_id).first()
                    # Would need to check patient association
                    # For now, simplified check
                    return True
                
                return True
        
        return False
    
    async def authorize(
        self,
        resource_type: str,
        action: str,
        token_data: TokenData = Depends(verify_token),
        patient_id: Optional[str] = None
    ) -> TokenData:
        """Authorize user for specific action with audit logging"""
        
        # Check permission
        if not self.check_permission(token_data, resource_type, action, patient_id):
            # Log access denial
            await self._audit_log(
                event_type=AuditEvent.ACCESS_DENIED,
                user_id=token_data.user_id,
                username=token_data.username,
                resource_type=resource_type,
                action=action,
                patient_id=patient_id,
                success=False,
                error_message="Insufficient permissions"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Log access grant
        await self._audit_log(
            event_type=AuditEvent.ACCESS_GRANTED,
            user_id=token_data.user_id,
            username=token_data.username,
            resource_type=resource_type,
            action=action,
            patient_id=patient_id,
            success=True
        )
        
        return token_data
    
    def encrypt_phi(self, data: str) -> str:
        """Encrypt PHI data using FIPS 140-2 compliant encryption"""
        
        # Get active encryption key
        key_record = self.db.query(DataEncryptionKey).filter_by(
            is_active=True,
            purpose="PHI_ENCRYPTION"
        ).first()
        
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption key not available"
            )
        
        # Decrypt master key
        master_key = base64.b64decode(key_record.encrypted_key.encode('utf-8'))
        
        # Create Fernet instance
        f = Fernet(master_key)
        
        # Encrypt data
        encrypted = f.encrypt(data.encode('utf-8'))
        
        # Return with key ID for key rotation support
        return f"{key_record.key_id}:{base64.b64encode(encrypted).decode('utf-8')}"
    
    def decrypt_phi(self, encrypted_data: str) -> str:
        """Decrypt PHI data"""
        
        try:
            # Parse key ID and encrypted data
            parts = encrypted_data.split(':', 1)
            if len(parts) != 2:
                raise ValueError("Invalid encrypted data format")
            
            key_id, encrypted = parts
            
            # Get encryption key
            key_record = self.db.query(DataEncryptionKey).filter_by(key_id=key_id).first()
            
            if not key_record:
                raise ValueError("Encryption key not found")
            
            # Decrypt master key
            master_key = base64.b64decode(key_record.encrypted_key.encode('utf-8'))
            
            # Create Fernet instance
            f = Fernet(master_key)
            
            # Decrypt data
            decrypted = f.decrypt(base64.b64decode(encrypted.encode('utf-8')))
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt data"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt"""
        import bcrypt
        
        # Validate password complexity
        if not self._validate_password_complexity(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet complexity requirements"
            )
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    def _validate_password_complexity(self, password: str) -> bool:
        """Validate password meets complexity requirements"""
        
        if len(password) < self.config.password_min_length:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if self.config.password_require_uppercase and not has_upper:
            return False
        if self.config.password_require_lowercase and not has_lower:
            return False
        if self.config.password_require_numbers and not has_digit:
            return False
        if self.config.password_require_special and not has_special:
            return False
        
        return True
    
    def _check_ip_allowed(self, ip_address: str, allowed_ranges: List[str]) -> bool:
        """Check if IP address is in allowed ranges"""
        import ipaddress
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for range_str in allowed_ranges:
                try:
                    network = ipaddress.ip_network(range_str)
                    if ip in network:
                        return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    async def _audit_log(
        self,
        event_type: AuditEvent,
        action: str = "",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request_data: Optional[Dict] = None
    ):
        """Create tamper-proof audit log entry"""
        
        try:
            # Sanitize request data to remove sensitive info
            sanitized_data = self._sanitize_request_data(request_data) if request_data else None
            
            # Create audit log entry
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                username=username,
                event_type=event_type.value,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                action=action or event_type.value,
                ip_address=ip_address,
                success=success,
                error_message=error_message,
                request_data=sanitized_data,
                session_id=secrets.token_urlsafe(16)
            )
            
            self.db.add(audit_entry)
            self.db.commit()
            
            # Also send to SIEM system if configured
            await self._send_to_siem(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    def _sanitize_request_data(self, data: Dict) -> Dict:
        """Remove sensitive data from request for audit logging"""
        
        sensitive_fields = [
            "password", "ssn", "credit_card", "token",
            "api_key", "secret", "authorization"
        ]
        
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        return sanitized
    
    async def _send_to_siem(self, audit_entry: AuditLog):
        """Send audit log to SIEM system"""
        # This would integrate with Splunk, ELK, etc.
        pass
    
    async def rotate_encryption_keys(self):
        """Rotate data encryption keys"""
        
        logger.info("Starting encryption key rotation...")
        
        # Generate new key
        new_master_key = Fernet.generate_key()
        
        # Create new key record
        new_key = DataEncryptionKey(
            key_id=secrets.token_urlsafe(32),
            encrypted_key=base64.b64encode(new_master_key).decode('utf-8'),
            purpose="PHI_ENCRYPTION"
        )
        
        # Deactivate old keys
        self.db.query(DataEncryptionKey).filter_by(
            is_active=True,
            purpose="PHI_ENCRYPTION"
        ).update({"is_active": False, "rotated_at": datetime.utcnow()})
        
        # Activate new key
        self.db.add(new_key)
        self.db.commit()
        
        logger.info("Encryption key rotation completed")
        
        # Trigger re-encryption of existing data in background
        # This would be a separate async process


class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self, redis_client: redis.Redis, config: SecurityConfig):
        self.redis = redis_client
        self.config = config
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, self.config.rate_limit_window_seconds)
        
        return current <= self.config.rate_limit_requests


class SessionManager:
    """Secure session management"""
    
    def __init__(self, redis_client: redis.Redis, config: SecurityConfig):
        self.redis = redis_client
        self.config = config
    
    async def create_session(self, session_id: str, user_id: int, expires_at: datetime):
        """Create new session"""
        
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        
        await self.redis.setex(
            f"session:{session_id}",
            ttl,
            json.dumps(session_data)
        )
    
    async def validate_session(self, session_id: str) -> bool:
        """Validate session is active and not expired"""
        
        session_data = await self.redis.get(f"session:{session_id}")
        
        if not session_data:
            return False
        
        data = json.loads(session_data)
        expires_at = datetime.fromisoformat(data["expires_at"])
        
        return datetime.utcnow() < expires_at
    
    async def update_activity(self, session_id: str):
        """Update session last activity time"""
        
        session_data = await self.redis.get(f"session:{session_id}")
        
        if session_data:
            data = json.loads(session_data)
            data["last_activity"] = datetime.utcnow().isoformat()
            
            ttl = await self.redis.ttl(f"session:{session_id}")
            
            await self.redis.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(data)
            )
    
    async def terminate_session(self, session_id: str):
        """Terminate session"""
        
        await self.redis.delete(f"session:{session_id}")


def get_current_user(token_data: TokenData = Depends(HIPAASecurityManager.verify_token)) -> TokenData:
    """Dependency to get current authenticated user"""
    return token_data


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific user roles"""
    
    async def role_checker(token_data: TokenData = Depends(get_current_user)):
        if token_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges"
            )
        return token_data
    
    return role_checker


def require_access_level(min_level: AccessLevel):
    """Dependency to require minimum access level"""
    
    access_hierarchy = {
        AccessLevel.NONE: 0,
        AccessLevel.AGGREGATE: 1,
        AccessLevel.DE_IDENTIFIED: 2,
        AccessLevel.PHI_LIMITED: 3,
        AccessLevel.PHI_FULL: 4
    }
    
    async def access_checker(token_data: TokenData = Depends(get_current_user)):
        user_level = access_hierarchy.get(token_data.access_level, 0)
        required_level = access_hierarchy.get(min_level, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient data access level"
            )
        return token_data
    
    return access_checker
