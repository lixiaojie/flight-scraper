"""
Dashboard API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.models.flight_data import FlightData

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard statistics"""
    
    try:
        # Get task statistics
        total_tasks = db.query(Task).count()
        running_tasks = db.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        failed_tasks = db.query(Task).filter(Task.status == TaskStatus.FAILED).count()
        
        # Get last execution time
        last_task = db.query(Task).order_by(Task.updated_at.desc()).first()
        last_execution_time = last_task.updated_at if last_task else None
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_tasks = db.query(Task).filter(
            Task.created_at >= yesterday
        ).count()
        
        # Get flight data statistics
        total_flights = db.query(FlightData).count()
        unique_airlines = db.query(FlightData.airline).distinct().count()
        
        # Get average price
        avg_price_result = db.query(func.avg(FlightData.price)).scalar()
        avg_price = float(avg_price_result) if avg_price_result else 0.0
        
        # Get lowest price
        lowest_price_result = db.query(func.min(FlightData.price)).scalar()
        lowest_price = float(lowest_price_result) if lowest_price_result else 0.0
        
        return {
            "task_stats": {
                "total": total_tasks,
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "recent_24h": recent_tasks
            },
            "flight_stats": {
                "total_flights": total_flights,
                "unique_airlines": unique_airlines,
                "average_price": avg_price,
                "lowest_price": lowest_price
            },
            "last_execution_time": last_execution_time,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/recent-tasks")
async def get_recent_tasks(
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent tasks"""
    
    try:
        tasks = db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
        
        return {
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "departure_city": task.departure_city,
                    "arrival_city": task.arrival_city,
                    "travel_date": task.travel_date,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                }
                for task in tasks
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent tasks: {str(e)}")


@router.get("/price-trends")
async def get_price_trends(
    days: int = 7,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get price trends over time"""
    
    try:
        # Get flight data from the last N days
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Group by date and get average prices
        price_trends = db.query(
            func.date(FlightData.scraped_at).label('date'),
            func.avg(FlightData.price).label('avg_price'),
            func.min(FlightData.price).label('min_price'),
            func.count(FlightData.id).label('flight_count')
        ).filter(
            FlightData.scraped_at >= start_date
        ).group_by(
            func.date(FlightData.scraped_at)
        ).order_by('date').all()
        
        return {
            "price_trends": [
                {
                    "date": trend.date.isoformat(),
                    "average_price": float(trend.avg_price),
                    "minimum_price": float(trend.min_price),
                    "flight_count": trend.flight_count
                }
                for trend in price_trends
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price trends: {str(e)}")
