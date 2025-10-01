"""
Authentication service
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password
import hashlib


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        # 尝试bcrypt验证
        try:
            if verify_password(password, user.hashed_password):
                return user
        except:
            pass
        
        # 如果bcrypt失败，尝试SHA256验证
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == user.hashed_password:
            return user
        
        return None
    
    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login time"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.last_login = datetime.utcnow()
        self.db.commit()
        return True
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        # This would decode the JWT token and get user
        # Implementation depends on JWT token handling
        # For now, return None as placeholder
        return None
