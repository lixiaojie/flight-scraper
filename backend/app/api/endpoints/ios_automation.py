from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.host_ios_service import HostIOSService
from app.schemas.ios_automation import (
    IOSAutomationRequest, 
    IOSAutomationResponse,
    IOSHealthResponse
)
import logging
import os
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=IOSHealthResponse)
async def health_check():
    """Check iOS automation service health"""
    try:
        # For host-based iOS automation, we just check if the main script exists
        import os
        script_path = "/app/ios_automation_main.py"
        
        if os.path.exists(script_path):
            return IOSHealthResponse(
                status="healthy",
                simulator="host_ios_available",
                timestamp=datetime.now().isoformat()
            )
        else:
            return IOSHealthResponse(
                status="unhealthy",
                simulator="script_not_found",
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        logger.error(f"iOS automation health check failed: {str(e)}")
        return IOSHealthResponse(
            status="unhealthy",
            simulator="error",
            timestamp=datetime.now().isoformat()
        )

@router.post("/start")
async def start_automation(
    request: IOSAutomationRequest,
    db: Session = Depends(get_db)
):
    """Start iOS automation session"""
    try:
        service = HostIOSService(db)
        response = service.start_automation(
            platform_id=request.platform_id,
            wait_time=request.wait_time,
            capture_screenshot=request.capture_screenshot
        )
        return response
    except Exception as e:
        logger.error(f"Failed to start iOS automation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """Get all iOS automation sessions"""
    try:
        service = HostIOSService(db)
        sessions = service.get_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to get iOS automation sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete iOS automation session"""
    try:
        service = HostIOSService(db)
        result = service.delete_session(session_id)
        return result
    except Exception as e:
        logger.error(f"Failed to delete iOS session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers")
async def get_containers(db: Session = Depends(get_db)):
    """Get all iOS containers"""
    try:
        service = HostIOSService(db)
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
        service = HostIOSService(db)
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
        service = HostIOSService(db)
        result = service.stop_container(container_id)
        return result
    except Exception as e:
        logger.error(f"Failed to stop iOS container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/containers/{container_id}")
async def delete_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Delete iOS simulator container"""
    try:
        service = HostIOSService(db)
        result = service.delete_container(container_id)
        return result
    except Exception as e:
        logger.error(f"Failed to delete iOS container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screenshots/ios/{filename}")
async def get_screenshot(filename: str):
    """Serve iOS automation screenshots"""
    try:
        screenshot_path = f"/app/screenshots/ios/{filename}"
        if os.path.exists(screenshot_path):
            return FileResponse(screenshot_path, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Screenshot not found")
    except Exception as e:
        logger.error(f"Failed to serve screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
