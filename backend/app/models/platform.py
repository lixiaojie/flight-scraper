"""
Platform and Account models for target platforms
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PlatformType(str, enum.Enum):
    """Platform type enumeration"""
    WEB = "web"
    MOBILE_APP = "mobile_app"


class Platform(Base):
    """Platform model for target platforms (websites/apps)"""
    
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    platform_type = Column(Enum(PlatformType), nullable=False)
    
    # Platform configuration
    base_url = Column(String(500), nullable=True)  # For websites
    bundle_id = Column(String(200), nullable=True)  # For mobile apps
    package_name = Column(String(200), nullable=True)  # For Android apps
    
    # Scraping configuration
    search_url_template = Column(Text, nullable=True)
    selectors = Column(Text, nullable=True)  # JSON string for CSS selectors
    headers = Column(Text, nullable=True)  # JSON string for HTTP headers
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="platform", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Platform(id={self.id}, name='{self.name}', type='{self.platform_type}')>"


class Account(Base):
    """Account model for platform accounts"""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(200), nullable=False)
    password = Column(String(500), nullable=False)  # Encrypted
    email = Column(String(200), nullable=True)
    
    # Account limits
    max_queries_per_day = Column(Integer, default=100)
    current_query_count = Column(Integer, default=0)
    last_query_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    platform = relationship("Platform", back_populates="accounts")
    
    def __repr__(self):
        return f"<Account(id={self.id}, username='{self.username}', platform='{self.platform.name if self.platform else None}')>"
