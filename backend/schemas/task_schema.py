"""
任务数据模式
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TaskRecordResponse(BaseModel):
    """任务记录响应模式"""
    id: int
    task_name: str
    task_type: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[int] = None
    success: bool
    flights_count: int
    error_message: Optional[str] = None
    source: str
    config: Optional[str] = None
    airline: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TaskStatisticsResponse(BaseModel):
    """任务统计响应模式"""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    running_tasks: int
    success_rate: float
    avg_duration: float
    total_flights: int


class CreateTaskRequest(BaseModel):
    """创建任务请求模式"""
    task_name: Optional[str] = None
    task_type: str = "flight_scraper"
    source: str = "12306"
    config: Optional[Dict[str, Any]] = None
    airline: Optional[str] = "深圳航空"
    notes: Optional[str] = None


class UpdateTaskResultRequest(BaseModel):
    """更新任务结果请求模式"""
    success: bool
    flights_count: int = 0
    error_message: Optional[str] = None
