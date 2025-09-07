"""
Android Automation API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.services.android_automation_service import AndroidAutomationService
from app.schemas.android_automation import (
    AutomationRequest, AutomationResponse, AndroidAutomationSessionResponse,
    AndroidContainerResponse, ContainerResourceInfo
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start", response_model=AutomationResponse)
async def start_automation(
    request: AutomationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start Android automation process"""
    try:
        service = AndroidAutomationService(db)
        
        # Start automation in background
        result = service.start_automation(request)
        
        # Schedule cleanup after completion
        if result.status in ["completed", "failed"]:
            background_tasks.add_task(service.cleanup_session, result.session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to start automation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[AndroidAutomationSessionResponse])
async def list_automation_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all automation sessions"""
    try:
        from app.models.android_automation import AndroidAutomationSession
        
        sessions = db.query(AndroidAutomationSession).offset(skip).limit(limit).all()
        return [AndroidAutomationSessionResponse.model_validate(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=AndroidAutomationSessionResponse)
async def get_automation_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get automation session details"""
    try:
        service = AndroidAutomationService(db)
        session = service.get_session_status(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return AndroidAutomationSessionResponse.model_validate(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def cleanup_automation_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Cleanup automation session and container"""
    try:
        service = AndroidAutomationService(db)
        success = service.cleanup_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers", response_model=List[AndroidContainerResponse])
async def list_containers(
    db: Session = Depends(get_db)
):
    """List all Android containers"""
    try:
        service = AndroidAutomationService(db)
        containers = service.list_containers()
        return containers
        
    except Exception as e:
        logger.error(f"Failed to list containers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers/{container_id}/resources", response_model=ContainerResourceInfo)
async def get_container_resources(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Get container resource usage"""
    try:
        service = AndroidAutomationService(db)
        resources = service.get_container_resources(container_id)
        return ContainerResourceInfo(**resources)
        
    except Exception as e:
        logger.error(f"Failed to get container resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_id}/stop")
async def stop_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Stop Android container"""
    try:
        import subprocess
        
        # Stop container
        stop_cmd = ["docker", "stop", container_id]
        result = subprocess.run(stop_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Failed to stop container: {result.stderr}")
        
        # Update database
        from app.models.android_automation import AndroidContainer
        from app.schemas.android_automation import ContainerStatus
        from datetime import datetime
        
        container = db.query(AndroidContainer).filter(
            AndroidContainer.container_id == container_id
        ).first()
        
        if container:
            container.status = ContainerStatus.STOPPED
            container.stopped_at = datetime.utcnow()
            db.commit()
        
        return {"message": "Container stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop container {container_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_id}/start")
async def start_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Start Android container"""
    try:
        import subprocess
        
        # Start container
        start_cmd = ["docker", "start", container_id]
        result = subprocess.run(start_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Failed to start container: {result.stderr}")
        
        # Update database
        from app.models.android_automation import AndroidContainer
        from app.schemas.android_automation import ContainerStatus
        from datetime import datetime
        
        container = db.query(AndroidContainer).filter(
            AndroidContainer.container_id == container_id
        ).first()
        
        if container:
            container.status = ContainerStatus.RUNNING
            container.started_at = datetime.utcnow()
            db.commit()
        
        return {"message": "Container started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start container {container_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        import subprocess
        
        # Check if Docker is running
        docker_cmd = ["docker", "version"]
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        
        docker_status = "running" if result.returncode == 0 else "not_running"
        
        return {
            "status": "healthy",
            "docker": docker_status,
            "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
