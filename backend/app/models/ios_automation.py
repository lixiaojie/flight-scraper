from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid

class AutomationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ContainerStatus(str, enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

class IOSAutomationSession(Base):
    __tablename__ = "ios_automation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    status = Column(Enum(AutomationStatus), default=AutomationStatus.PENDING)
    container_id = Column(String(100), nullable=True)
    container_name = Column(String(100), nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    wait_time = Column(Integer, default=5)
    capture_screenshot = Column(Boolean, default=True)
    execution_time = Column(Integer, default=0)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    platform = relationship("Platform", back_populates="ios_automation_sessions")

class IOSContainer(Base):
    __tablename__ = "ios_containers"
    
    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(100), unique=True, index=True)  # Simulator UDID
    container_name = Column(String(100), nullable=False)
    device_type = Column(String(100), nullable=False)  # e.g., "iPhone 16 Pro"
    status = Column(Enum(ContainerStatus), default=ContainerStatus.STOPPED)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
