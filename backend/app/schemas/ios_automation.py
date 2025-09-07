from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class IOSAutomationRequest(BaseModel):
    platform_id: int
    wait_time: int = 5
    capture_screenshot: bool = True

class IOSAutomationResponse(BaseModel):
    session_id: str
    status: str
    message: str
    screenshot_url: Optional[str] = None
    container_id: Optional[str] = None
    logs: Optional[str] = None
    execution_time: float

class IOSSessionInfo(BaseModel):
    session_id: str
    platform_id: int
    status: str
    container_id: Optional[str] = None
    screenshot_url: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

class IOSContainerInfo(BaseModel):
    container_id: str
    container_name: str
    device_type: str
    status: str
    is_active: bool
    created_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None

class IOSHealthResponse(BaseModel):
    status: str
    simulator: str
    timestamp: str
