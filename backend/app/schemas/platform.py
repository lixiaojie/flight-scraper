"""
Platform Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.platform import PlatformType


class PlatformBase(BaseModel):
    """Base platform schema"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    platform_type: PlatformType
    base_url: Optional[str] = None
    bundle_id: Optional[str] = None
    package_name: Optional[str] = None
    search_url_template: Optional[str] = None
    selectors: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    is_active: bool = True


class PlatformCreate(PlatformBase):
    """Schema for creating a platform"""
    pass


class PlatformUpdate(BaseModel):
    """Schema for updating a platform"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    bundle_id: Optional[str] = None
    package_name: Optional[str] = None
    search_url_template: Optional[str] = None
    selectors: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class PlatformResponse(PlatformBase):
    """Schema for platform response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AccountBase(BaseModel):
    """Base account schema"""
    username: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=1, max_length=500)
    email: Optional[str] = None
    max_queries_per_day: int = Field(default=100, ge=1, le=10000)
    is_active: bool = True
    is_verified: bool = False


class AccountCreate(AccountBase):
    """Schema for creating an account"""
    pass


class AccountResponse(AccountBase):
    """Schema for account response"""
    id: int
    platform_id: int
    current_query_count: int
    last_query_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PlatformWithAccounts(PlatformResponse):
    """Platform response with accounts"""
    accounts: List[AccountResponse] = []
