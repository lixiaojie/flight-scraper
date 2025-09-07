"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        existing_user = await auth_service.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create new user
        user = await auth_service.create_user(user_data)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    
    try:
        auth_service = AuthService(db)
        
        # Authenticate user
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Update last login
        await auth_service.update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during login: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Session = Depends(get_db)
):
    """Get current user information"""
    # This is a placeholder - proper JWT token validation would be implemented here
    # For now, return a mock user
    return UserResponse(
        id=1,
        username="admin",
        email="admin@example.com",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}
