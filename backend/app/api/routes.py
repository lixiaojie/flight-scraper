"""
Main API router configuration
"""

from fastapi import APIRouter
from app.api.endpoints import tasks, platforms, dashboard, auth, comparison

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)

api_router.include_router(
    platforms.router,
    prefix="/platforms",
    tags=["platforms"]
)

api_router.include_router(
    comparison.router,
    prefix="/comparison",
    tags=["comparison"]
)
