"""
管理员账号模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import hashlib

Base = declarative_base()

class Admin(Base):
    """管理员账号模型"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    email = Column(String(100), unique=True, comment='邮箱')
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_superuser = Column(Boolean, default=False, comment='是否超级管理员')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    last_login = Column(DateTime, comment='最后登录时间')
    
    def __repr__(self):
        return f"<Admin(username='{self.username}')>"
    
    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
