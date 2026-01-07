"""
航班数据模式
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FlightResultResponse(BaseModel):
    """航班结果响应模式"""
    id: int
    airline: str
    flight_number: str
    is_shared_flight: Optional[str] = None
    aircraft_type: Optional[str] = None
    departure_date: Optional[str] = None
    departure_time: str
    departure_airport: str
    departure_city: Optional[str] = None
    arrival_time: str
    arrival_airport: str
    arrival_city: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    flight_duration: Optional[str] = None
    has_stopover: Optional[str] = None
    stopover_city: Optional[str] = None
    stopover_airport: Optional[str] = None
    price: float
    currency: str = "CNY"
    cabin_class: Optional[str] = None
    discount_rate: Optional[str] = None
    original_price: Optional[float] = None
    task_id: Optional[int] = None
    scrape_time: Optional[str] = None
    source: str
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class FlightStatisticsResponse(BaseModel):
    """航班统计响应模式"""
    total_flights: int
    min_price: float
    max_price: float
    avg_price: float


class FlightSearchRequest(BaseModel):
    """航班搜索请求模式"""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    airline: Optional[str] = None
    departure_time_start: Optional[str] = None
    departure_time_end: Optional[str] = None
    limit: int = 50


class FlightSaveRequest(BaseModel):
    """航班保存请求模式"""
    flights: List[dict]
    source: str = "12306"
