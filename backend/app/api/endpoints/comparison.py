"""
Flight comparison API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.comparison_service import ComparisonService

router = APIRouter()


@router.get("/tasks/{task_id}/best-deals")
async def get_best_deals(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get best flight deals for a specific task"""
    
    try:
        comparison_service = ComparisonService(db)
        results = comparison_service.find_best_deals(task_id)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding best deals: {str(e)}")


@router.get("/price-trends")
async def get_price_trends(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get price trends over time"""
    
    try:
        comparison_service = ComparisonService(db)
        trends = comparison_service.get_price_trends(days)
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting price trends: {str(e)}")


@router.get("/similar-routes")
async def get_similar_routes(
    departure_city: str = Query(..., description="Departure city"),
    arrival_city: str = Query(..., description="Arrival city"),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Find similar routes and their historical prices"""
    
    try:
        comparison_service = ComparisonService(db)
        routes = comparison_service.find_similar_routes(departure_city, arrival_city, days)
        return routes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar routes: {str(e)}")
