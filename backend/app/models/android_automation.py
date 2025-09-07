from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class AndroidAutomationSession(Base):
    """Model for Android automation sessions"""
    __tablename__ = "android_automation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    container_id = Column(String(100), nullable=True)  # Docker container ID
    container_name = Column(String(100), nullable=True)  # Docker container name
    
    # App information
    app_package = Column(String(200), nullable=True)  # e.g., com.chinarailway.globalticketing
    app_version = Column(String(50), nullable=True)  # e.g., 5.9.4.5
    apk_path = Column(String(500), nullable=True)  # Local path to APK file
    
    # Screenshot information
    screenshot_path = Column(String(500), nullable=True)  # Local path to screenshot
    screenshot_url = Column(String(1000), nullable=True)  # Public URL for screenshot
    
    # Execution details
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)  # JSON string of execution logs
    
    # Resource information
    cpu_usage = Column(String(50), nullable=True)
    memory_usage = Column(String(50), nullable=True)
    disk_usage = Column(String(50), nullable=True)
    
    # Relationships
    platform = relationship("Platform", back_populates="automation_sessions")
    
    def __repr__(self):
        return f"<AndroidAutomationSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class AndroidContainer(Base):
    """Model for tracking Android containers"""
    __tablename__ = "android_containers"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(100), unique=True, index=True, nullable=False)
    container_name = Column(String(100), unique=True, index=True, nullable=False)
    image_name = Column(String(200), nullable=False)  # e.g., budtmo/docker-android
    image_tag = Column(String(100), nullable=False)  # e.g., api_30_x86
    
    # Container status
    status = Column(String(50), nullable=False, default="stopped")  # stopped, running, error
    is_active = Column(Boolean, default=True)
    
    # Resource allocation
    cpu_limit = Column(String(50), nullable=True)  # e.g., "2.0"
    memory_limit = Column(String(50), nullable=True)  # e.g., "4g"
    disk_limit = Column(String(50), nullable=True)  # e.g., "10g"
    
    # Network configuration
    host_port = Column(Integer, nullable=True)  # Port mapping for ADB
    container_port = Column(Integer, nullable=True, default=5555)  # ADB port in container
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    automation_sessions = relationship("AndroidAutomationSession", back_populates="container")
    
    def __repr__(self):
        return f"<AndroidContainer(id={self.id}, container_id='{self.container_id}', status='{self.status}')>"
