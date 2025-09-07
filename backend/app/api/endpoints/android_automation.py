"""
Android Automation API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.services.android_automation_service import AndroidAutomationService
from app.services.mock_android_automation_service import MockAndroidAutomationService
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
        # Check if we should use mock service (when Docker is not available)
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        if use_mock:
            service = MockAndroidAutomationService(db)
            logger.info("Using mock Android automation service")
        else:
            service = AndroidAutomationService(db)
            logger.info("Using real Android automation service")
        
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
        # Check if we should use mock service (when Docker is not available)
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        if use_mock:
            service = MockAndroidAutomationService(db)
            logger.info("Using mock Android automation service for cleanup")
        else:
            service = AndroidAutomationService(db)
            logger.info("Using real Android automation service for cleanup")
        
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
        # Check if we should use mock service
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        if use_mock:
            # Mock mode - return mock resource data
            from app.models.android_automation import AndroidContainer
            
            container = db.query(AndroidContainer).filter(
                AndroidContainer.container_id == container_id
            ).first()
            
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            # Return mock resource data
            mock_resources = {
                "container_id": container_id,
                "cpu_usage": "15.2%" if container.status == "running" else "0%",
                "memory_usage": "2.1GB / 4GB" if container.status == "running" else "0GB / 4GB",
                "disk_usage": "8.5GB / 20GB",
                "network_usage": "1.2MB/s" if container.status == "running" else "0MB/s",
                "uptime": "2h 15m" if container.status == "running" else "0s",
                "status": container.status
            }
            
            return ContainerResourceInfo(**mock_resources)
        else:
            # Real mode - use actual service
            service = AndroidAutomationService(db)
            resources = service.get_container_resources(container_id)
            return ContainerResourceInfo(**resources)
        
    except HTTPException:
        raise
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
        # Check if we should use mock service
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        if use_mock:
            # Mock mode - just update database
            from app.models.android_automation import AndroidContainer
            from app.schemas.android_automation import ContainerStatus
            from datetime import datetime
            
            container = db.query(AndroidContainer).filter(
                AndroidContainer.container_id == container_id
            ).first()
            
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            container.status = ContainerStatus.STOPPED
            container.stopped_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Mock container {container_id} stopped")
            return {"message": "Container stopped successfully (mock mode)"}
        else:
            # Real mode - use Docker
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
        # Check if we should use mock service
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        if use_mock:
            # Mock mode - just update database
            from app.models.android_automation import AndroidContainer
            from app.schemas.android_automation import ContainerStatus
            from datetime import datetime
            
            container = db.query(AndroidContainer).filter(
                AndroidContainer.container_id == container_id
            ).first()
            
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            container.status = ContainerStatus.RUNNING
            container.started_at = datetime.utcnow()
            container.stopped_at = None
            db.commit()
            
            logger.info(f"Mock container {container_id} started")
            return {"message": "Container started successfully (mock mode)"}
        else:
            # Real mode - use Docker
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
                container.stopped_at = None
                db.commit()
            
            return {"message": "Container started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start container {container_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/containers/{container_id}")
async def delete_container(
    container_id: str,
    db: Session = Depends(get_db)
):
    """Delete Android container"""
    try:
        # Check if we should use mock service
        import os
        use_mock = os.environ.get("USE_MOCK_ANDROID_AUTOMATION", "false").lower() == "true"
        
        # First, check if container exists and get its status
        from app.models.android_automation import AndroidContainer
        
        container = db.query(AndroidContainer).filter(
            AndroidContainer.container_id == container_id
        ).first()
        
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")
        
        # Only allow deletion of stopped containers
        if container.status == "running":
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete running container. Please stop it first."
            )
        
        if use_mock:
            # Mock mode - just delete from database
            # Also clean up any associated sessions
            from app.models.android_automation import AndroidAutomationSession
            
            # Find and delete associated sessions
            sessions = db.query(AndroidAutomationSession).filter(
                AndroidAutomationSession.container_id == container_id
            ).all()
            
            for session in sessions:
                db.delete(session)
            
            # Delete the container
            db.delete(container)
            db.commit()
            
            logger.info(f"Mock container {container_id} deleted along with {len(sessions)} associated sessions")
            return {"message": f"Container deleted successfully (mock mode). Removed {len(sessions)} associated sessions."}
        else:
            # Real mode - use Docker to remove container
            import subprocess
            
            # Remove container
            remove_cmd = ["docker", "rm", "-f", container_id]
            result = subprocess.run(remove_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=f"Failed to delete container: {result.stderr}")
            
            # Clean up associated sessions
            from app.models.android_automation import AndroidAutomationSession
            
            sessions = db.query(AndroidAutomationSession).filter(
                AndroidAutomationSession.container_id == container_id
            ).all()
            
            for session in sessions:
                db.delete(session)
            
            # Delete the container from database
            db.delete(container)
            db.commit()
            
            logger.info(f"Container {container_id} deleted along with {len(sessions)} associated sessions")
            return {"message": f"Container deleted successfully. Removed {len(sessions)} associated sessions."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete container {container_id}: {str(e)}")
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
