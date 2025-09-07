"""
Task model for flight scraping tasks
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Task type enumeration"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class TaskValidity(str, enum.Enum):
    """Task validity enumeration"""
    SCHEDULED = "scheduled"
    INSTANT = "instant"


class Task(Base):
    """Task model for flight scraping tasks"""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Task configuration
    departure_city = Column(String(100), nullable=False)
    arrival_city = Column(String(100), nullable=False)
    travel_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    num_travelers = Column(Integer, default=1)
    cabin_class = Column(String(50), default="economy")
    
    # Task scheduling
    task_type = Column(Enum(TaskType), default=TaskType.ONE_TIME)
    task_validity = Column(Enum(TaskValidity), default=TaskValidity.INSTANT)
    scheduled_time = Column(DateTime, nullable=True)
    frequency = Column(String(50), nullable=True)  # For recurring tasks
    
    # Task status
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="tasks")
    
    flight_data = relationship("FlightData", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', status='{self.status}')>"
