"""
航班API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from backend.core.database import get_db
from backend.services.flight_service import FlightService
from backend.models.flight_result import FlightResult
from backend.schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse

router = APIRouter(prefix="/flights", tags=["flights"])

@router.get("/", response_model=List[FlightResultResponse])
async def get_flights(
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    airline: Optional[str] = Query(None, description="航空公司"),
    limit: int = Query(50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取航班列表"""
    try:
        flight_service = FlightService(db)
        
        if min_price is not None and max_price is not None:
            flights = flight_service.get_flights_by_price_range(min_price, max_price)
        elif airline:
            flights = flight_service.get_flights_by_airline(airline)
        else:
            flights = flight_service.get_latest_flights(limit)
        
        return [flight.to_dict() for flight in flights]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", response_model=FlightStatisticsResponse)
async def get_flight_statistics(db: Session = Depends(get_db)):
    """获取航班统计信息"""
    try:
        flight_service = FlightService(db)
        stats = flight_service.get_flight_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-date")
async def get_flights_by_date(
    date: str = Query(..., description="日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """根据日期查询航班"""
    try:
        flight_service = FlightService(db)
        target_date = datetime.strptime(date, "%Y-%m-%d")
        flights = flight_service.get_flights_by_date(target_date)
        
        return [flight.to_dict() for flight in flights]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-time-range")
async def get_flights_by_time_range(
    start_time: str = Query(..., description="开始时间 (HH:MM)"),
    end_time: str = Query(..., description="结束时间 (HH:MM)"),
    db: Session = Depends(get_db)
):
    """根据时间范围查询航班"""
    try:
        flight_service = FlightService(db)
        flights = flight_service.get_flights_by_time_range(start_time, end_time)
        
        return [flight.to_dict() for flight in flights]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_old_flights(
    days: int = Query(7, description="保留天数"),
    db: Session = Depends(get_db)
):
    """清理旧航班数据"""
    try:
        flight_service = FlightService(db)
        deleted_count = flight_service.delete_old_flights(days)
        
        return {"message": f"成功删除 {deleted_count} 条旧航班数据"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-save")
async def batch_save_flights(
    flights: List[dict],
    source: str = "12306",
    db: Session = Depends(get_db)
):
    """批量保存航班数据"""
    try:
        flight_service = FlightService(db)
        saved_flights = flight_service.save_flight_results(flights, source)
        
        return {
            "message": f"成功保存 {len(saved_flights)} 条航班数据",
            "saved_count": len(saved_flights)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
