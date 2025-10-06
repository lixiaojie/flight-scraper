"""
管理员数据模式
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class AdminLoginRequest(BaseModel):
    """管理员登录请求模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class AdminCreateRequest(BaseModel):
    """创建管理员请求模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    is_superuser: bool = Field(False, description="是否超级管理员")

class AdminResponse(BaseModel):
    """管理员响应模式"""
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    """密码修改请求模式"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., description="新密码")
