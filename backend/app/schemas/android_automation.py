from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AutomationStatus(str, Enum):
    """Automation session status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ContainerStatus(str, Enum):
    """Container status enumeration"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class AndroidAutomationSessionBase(BaseModel):
    """Base schema for Android automation session"""
    platform_id: int = Field(..., description="Platform ID for the automation session")
    app_package: Optional[str] = Field(None, max_length=200, description="Android app package name")
    app_version: Optional[str] = Field(None, max_length=50, description="App version")
    
    class Config:
        from_attributes = True


class AndroidAutomationSessionCreate(AndroidAutomationSessionBase):
    """Schema for creating Android automation session"""
    pass


class AndroidAutomationSessionUpdate(BaseModel):
    """Schema for updating Android automation session"""
    status: Optional[AutomationStatus] = None
    container_id: Optional[str] = Field(None, max_length=100)
    container_name: Optional[str] = Field(None, max_length=100)
    app_package: Optional[str] = Field(None, max_length=200)
    app_version: Optional[str] = Field(None, max_length=50)
    apk_path: Optional[str] = Field(None, max_length=500)
    screenshot_path: Optional[str] = Field(None, max_length=500)
    screenshot_url: Optional[str] = Field(None, max_length=1000)
    error_message: Optional[str] = None
    logs: Optional[str] = None
    cpu_usage: Optional[str] = Field(None, max_length=50)
    memory_usage: Optional[str] = Field(None, max_length=50)
    disk_usage: Optional[str] = Field(None, max_length=50)
    end_time: Optional[datetime] = None


class AndroidAutomationSessionResponse(AndroidAutomationSessionBase):
    """Schema for Android automation session response"""
    id: int
    session_id: str
    status: AutomationStatus
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    apk_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    screenshot_url: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    logs: Optional[str] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    disk_usage: Optional[str] = None
    
    class Config:
        from_attributes = True


class AndroidContainerBase(BaseModel):
    """Base schema for Android container"""
    container_name: str = Field(..., max_length=100, description="Container name")
    image_name: str = Field(..., max_length=200, description="Docker image name")
    image_tag: str = Field(..., max_length=100, description="Docker image tag")
    cpu_limit: Optional[str] = Field(None, max_length=50, description="CPU limit")
    memory_limit: Optional[str] = Field(None, max_length=50, description="Memory limit")
    disk_limit: Optional[str] = Field(None, max_length=50, description="Disk limit")
    host_port: Optional[int] = Field(None, description="Host port for ADB")
    container_port: Optional[int] = Field(5555, description="Container ADB port")
    
    class Config:
        from_attributes = True


class AndroidContainerCreate(AndroidContainerBase):
    """Schema for creating Android container"""
    pass


class AndroidContainerUpdate(BaseModel):
    """Schema for updating Android container"""
    status: Optional[ContainerStatus] = None
    is_active: Optional[bool] = None
    cpu_limit: Optional[str] = Field(None, max_length=50)
    memory_limit: Optional[str] = Field(None, max_length=50)
    disk_limit: Optional[str] = Field(None, max_length=50)
    host_port: Optional[int] = None
    container_port: Optional[int] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


class AndroidContainerResponse(AndroidContainerBase):
    """Schema for Android container response"""
    id: int
    container_id: str
    status: ContainerStatus
    is_active: bool
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AutomationRequest(BaseModel):
    """Schema for automation request"""
    platform_id: int = Field(..., description="Platform ID to automate")
    app_package: Optional[str] = Field(None, max_length=200, description="App package name")
    app_version: Optional[str] = Field(None, max_length=50, description="App version")
    apk_url: Optional[str] = Field(None, max_length=1000, description="APK download URL")
    wait_time: Optional[int] = Field(30, description="Wait time for app to load (seconds)")
    capture_screenshot: Optional[bool] = Field(True, description="Whether to capture screenshot")
    
    @validator('wait_time')
    def validate_wait_time(cls, v):
        if v is not None and (v < 5 or v > 300):
            raise ValueError('Wait time must be between 5 and 300 seconds')
        return v


class AutomationResponse(BaseModel):
    """Schema for automation response"""
    session_id: str
    status: AutomationStatus
    message: str
    screenshot_url: Optional[str] = None
    container_id: Optional[str] = None
    logs: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None  # in seconds


class ContainerResourceInfo(BaseModel):
    """Schema for container resource information"""
    container_id: str
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    disk_usage: Optional[str] = None
    network_usage: Optional[str] = None
    uptime: Optional[str] = None
    status: str
