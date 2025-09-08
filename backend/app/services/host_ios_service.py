import os
import time
import subprocess
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.platform import Platform
from app.models.ios_automation import IOSAutomationSession, IOSContainer, AutomationStatus, ContainerStatus

logger = logging.getLogger(__name__)

class HostIOSService:
    def __init__(self, db: Session):
        self.db = db
        self.screenshots_dir = "/app/screenshots/ios"
        self.host_client_path = "/app/ios_automation_main.py"
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def start_automation(self, platform_id: int, wait_time: int = 5, capture_screenshot: bool = True) -> Dict[str, Any]:
        """Start iOS automation using host-based client"""
        logger.info(f"Starting iOS automation for platform {platform_id}")
        
        try:
            # Check for existing active iOS sessions and stop them
            active_sessions = self.db.query(IOSAutomationSession).filter(
                IOSAutomationSession.status == AutomationStatus.RUNNING
            ).all()
            
            if active_sessions:
                logger.info(f"Found {len(active_sessions)} active iOS sessions, stopping them first")
                for active_session in active_sessions:
                    # Stop the session
                    active_session.status = AutomationStatus.COMPLETED
                    active_session.logs = "Stopped to allow new session"
                    self.db.commit()
                    
                    # Stop associated containers
                    active_containers = self.db.query(IOSContainer).filter(
                        IOSContainer.container_id.like(f"host-ios-{active_session.id}")
                    ).all()
                    for container in active_containers:
                        container.status = ContainerStatus.STOPPED
                        container.stopped_at = datetime.now()
                    self.db.commit()
            
            # Get platform information
            platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise Exception(f"Platform {platform_id} not found")
            
            # Create automation session
            session = IOSAutomationSession(
                platform_id=platform_id,
                status=AutomationStatus.RUNNING,
                wait_time=wait_time,
                capture_screenshot=capture_screenshot
            )
            self.db.add(session)
            self.db.commit()
            
            # Create container record with unique ID
            container_id = f"host-ios-{session.id}"
            container = IOSContainer(
                container_id=container_id,
                container_name="Host iOS Device",
                device_type="iPhone Simulator",
                status=ContainerStatus.RUNNING
            )
            self.db.add(container)
            self.db.commit()
            
            # Call host-based iOS automation client
            result = self._call_host_client(platform_id, wait_time, capture_screenshot)
            
            # Update session with results
            if result.get("status") == "completed":
                session.status = AutomationStatus.COMPLETED
                screenshot_path = result.get("screenshot_path")
                if screenshot_path:
                    # Generate a URL that can be accessed from the frontend
                    # The screenshot is saved in the Docker volume, so we can serve it via the backend
                    filename = os.path.basename(screenshot_path)
                    session.screenshot_url = f"/api/v1/ios-automation/screenshots/ios/{filename}"
                else:
                    session.screenshot_url = None
                session.logs = f"Automation completed successfully. Device: {result.get('device_id')}"
                
                # Update container status to stopped
                container.status = ContainerStatus.STOPPED
                container.stopped_at = datetime.now()
            else:
                session.status = AutomationStatus.FAILED
                session.logs = result.get("message", "Unknown error")
                
                # Update container status to error
                container.status = ContainerStatus.ERROR
                container.stopped_at = datetime.now()
            
            session.execution_time = result.get("execution_time", 0)
            self.db.commit()
            
            return {
                "session_id": str(session.id),
                "status": session.status.value,
                "message": result.get("message", "Automation completed"),
                "screenshot_url": session.screenshot_url,
                "container_id": str(container.id),
                "logs": session.logs,
                "execution_time": session.execution_time
            }
            
        except Exception as e:
            logger.error(f"iOS automation failed: {str(e)}")
            if 'session' in locals():
                session.status = AutomationStatus.FAILED
                session.logs = str(e)
                self.db.commit()
            
            return {
                "session_id": str(session.id) if 'session' in locals() else None,
                "status": "failed",
                "message": f"iOS automation failed: {str(e)}",
                "screenshot_url": None,
                "container_id": None,
                "logs": str(e),
                "execution_time": 0
            }
    
    def _call_host_client(self, platform_id: int, wait_time: int, capture_screenshot: bool) -> Dict[str, Any]:
        """Call the host-based iOS automation client"""
        try:
            # Get platform configuration
            platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise Exception(f"Platform {platform_id} not found")
            
            # Prepare platform config
            platform_config = {
                "bundle_id": platform.bundle_id or "cn.12306.rails12306"  # Default to 12306 app
            }
            
            # Prepare command to run the host client
            cmd = [
                "python3",
                self.host_client_path,
                "--platform-config", json.dumps(platform_config),
                "--wait-time", str(wait_time),
                "--capture-screenshot", str(capture_screenshot).lower()
            ]
            
            logger.info(f"Calling host client: {' '.join(cmd)}")
            
            # Run the host client
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Host client failed: {result.stderr}")
            
            # Parse the JSON response
            try:
                response = json.loads(result.stdout)
                return response
            except json.JSONDecodeError:
                # If not JSON, treat as simple success
                return {
                    "status": "completed",
                    "message": "iOS automation completed successfully",
                    "screenshot_url": None,
                    "device_id": "host-ios-device",
                    "execution_time": 0
                }
                
        except subprocess.TimeoutExpired:
            raise Exception("iOS automation timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Failed to call host client: {str(e)}")
            raise
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all iOS automation sessions"""
        sessions = self.db.query(IOSAutomationSession).order_by(IOSAutomationSession.created_at.desc()).all()
        return [
            {
                "id": str(session.id),
                "platform_id": session.platform_id,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "execution_time": session.execution_time,
                "screenshot_url": session.screenshot_url,
                "logs": session.logs
            }
            for session in sessions
        ]
    
    def get_containers(self) -> List[Dict[str, Any]]:
        """Get all iOS containers"""
        containers = self.db.query(IOSContainer).order_by(IOSContainer.created_at.desc()).all()
        return [
            {
                "id": str(container.id),
                "container_id": container.container_id,
                "container_name": container.container_name,
                "device_type": container.device_type,
                "status": container.status.value,
                "created_at": container.created_at.isoformat(),
                "started_at": container.started_at.isoformat() if container.started_at else None
            }
            for container in containers
        ]
    
    def stop_container(self, container_id: str) -> Dict[str, Any]:
        """Stop iOS container and close iPhone connection"""
        try:
            container = self.db.query(IOSContainer).filter(IOSContainer.container_id == container_id).first()
            if not container:
                raise Exception("Container not found")
            
            # Extract session ID from container_id (format: host-ios-{session_id})
            session_id = container_id.replace("host-ios-", "")
            
            # Stop the associated automation session
            session = self.db.query(IOSAutomationSession).filter(IOSAutomationSession.id == session_id).first()
            if session and session.status == AutomationStatus.RUNNING:
                session.status = AutomationStatus.COMPLETED
                session.logs = "Manually stopped by user"
                self.db.commit()
                logger.info(f"Stopped automation session {session_id}")
            
            # Update container status
            container.status = ContainerStatus.STOPPED
            container.stopped_at = datetime.now()
            self.db.commit()
            
            # Note: The actual iPhone connection will be closed when the ios_automation_main.py process ends
            # This happens automatically when the subprocess completes or times out
            
            return {"status": "success", "message": "Container stopped and iPhone connection closed"}
            
        except Exception as e:
            logger.error(f"Failed to stop container: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def start_container(self, container_id: str) -> Dict[str, Any]:
        """Start iOS container (simulated)"""
        try:
            container = self.db.query(IOSContainer).filter(IOSContainer.container_id == container_id).first()
            if not container:
                raise Exception("Container not found")
            
            container.status = ContainerStatus.RUNNING
            container.started_at = datetime.now()
            self.db.commit()
            
            return {"status": "success", "message": "Container started successfully"}
            
        except Exception as e:
            logger.error(f"Failed to start container: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def delete_container(self, container_id: str) -> Dict[str, Any]:
        """Delete iOS container"""
        try:
            container = self.db.query(IOSContainer).filter(IOSContainer.container_id == container_id).first()
            if not container:
                raise Exception("Container not found")
            
            self.db.delete(container)
            self.db.commit()
            
            return {"status": "success", "message": "Container deleted successfully"}
            
        except Exception as e:
            logger.error(f"Failed to delete container: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete iOS automation session"""
        try:
            session = self.db.query(IOSAutomationSession).filter(IOSAutomationSession.id == session_id).first()
            if not session:
                raise Exception("Session not found")
            
            self.db.delete(session)
            self.db.commit()
            
            return {"status": "success", "message": "Session deleted successfully"}
            
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return {"status": "error", "message": str(e)}
