from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ios_automation_service import IOSAutomationService
from app.schemas.ios_automation import (
    IOSAutomationRequest, 
    IOSAutomationResponse,
    IOSHealthResponse
)
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=IOSHealthResponse)
async def health_check():
    """Check iOS automation service health"""
    try:
        import subprocess
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "--json"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            return IOSHealthResponse(
                status="healthy",
                simulator="available",
                timestamp=datetime.now().isoformat()
            )
        else:
            return IOSHealthResponse(
                status="unhealthy",
                simulator="unavailable",
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        logger.error(f"iOS automation health check failed: {str(e)}")
        return IOSHealthResponse(
            status="unhealthy",
            simulator="error",
            timestamp=datetime.now().isoformat()
        )

@router.post("/start", response_model=IOSAutomationResponse)
async def start_automation(
    request: IOSAutomationRequest,
    db: Session = Depends(get_db)
):
    """Start iOS automation session"""
    try:
        service = IOSAutomationService(db)
        response = service.start_automation(request)
        return response
    except Exception as e:
        logger.error(f"Failed to start iOS automation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """Get all iOS automation sessions"""
    try:
        service = IOSAutomationService(db)
        sessions = service.get_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to get iOS automation sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers")
async def get_containers(db: Session = Depends(get_db)):
    """Get all iOS containers"""
    try:
        service = IOSAutomationService(db)
        containers = service.get_containers()
        return {"containers": containers}
    except Exception as e:
        logger.error(f"Failed to get iOS containers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_id}/start")
async def start_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Start iOS simulator container"""
    try:
        service = IOSAutomationService(db)
        result = service.start_container(container_id)
        return result
    except Exception as e:
        logger.error(f"Failed to start iOS container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_id}/stop")
async def stop_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Stop iOS simulator container"""
    try:
        service = IOSAutomationService(db)
        result = service.stop_container(container_id)
        return result
    except Exception as e:
        logger.error(f"Failed to stop iOS container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
