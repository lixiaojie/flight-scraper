"""
Mock Android Automation Service for development/testing
This service simulates Android automation without requiring Docker
"""

import os
import json
import time
import uuid
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.android_automation import AndroidAutomationSession, AndroidContainer
from app.models.platform import Platform
from app.schemas.android_automation import (
    AutomationRequest, AutomationResponse, AutomationStatus,
    AndroidContainerCreate, AndroidContainerResponse, ContainerStatus
)
import logging

logger = logging.getLogger(__name__)


class MockAndroidAutomationService:
    """Mock service for Android automation operations (development/testing)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.screenshots_dir = "/app/screenshots"
        self.apk_download_dir = "/app/downloads"
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.apk_download_dir, exist_ok=True)
    
    def start_automation(self, request: AutomationRequest) -> AutomationResponse:
        """Start mock Android automation process"""
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Get platform information first
            platform = self.db.query(Platform).filter(Platform.id == request.platform_id).first()
            if not platform:
                raise ValueError(f"Platform with ID {request.platform_id} not found")
            
            # Validate platform configuration
            if platform.platform_type != "mobile_app":
                raise ValueError(f"Platform {platform.name} is not a mobile app platform")
            
            if not platform.bundle_id:
                raise ValueError(f"Platform {platform.name} has no bundle ID configured")
            
            if not platform.download_url:
                raise ValueError(f"Platform {platform.name} has no download URL configured")
            
            # Use platform settings as primary source
            app_package = request.app_package or platform.bundle_id
            app_version = request.app_version or "latest"
            apk_url = request.apk_url or platform.download_url
            
            logger.info(f"Mock automation using platform settings for {platform.name}:")
            logger.info(f"  - App Package: {app_package}")
            logger.info(f"  - App Version: {app_version}")
            logger.info(f"  - APK URL: {apk_url}")
            
            # Create automation session
            session = AndroidAutomationSession(
                session_id=session_id,
                platform_id=request.platform_id,
                status=AutomationStatus.PENDING,
                app_package=app_package,
                app_version=app_version
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Created mock automation session {session_id}")
            
            # Simulate automation steps
            self._simulate_container_setup(session, platform)
            self._simulate_apk_download(session, platform, apk_url)
            screenshot_url = self._simulate_screenshot_capture(session, platform, request.wait_time)
            
            # Update session as completed
            execution_time = time.time() - start_time
            session.status = AutomationStatus.COMPLETED
            session.end_time = datetime.utcnow()
            session.screenshot_url = screenshot_url
            session.logs = json.dumps({
                "execution_time": execution_time,
                "steps_completed": ["mock_container_setup", "mock_apk_download", "mock_screenshot_capture"],
                "container_id": f"mock-container-{session_id[:8]}",
                "mock_mode": True
            })
            
            self.db.commit()
            
            return AutomationResponse(
                session_id=session_id,
                status=AutomationStatus.COMPLETED,
                message="Mock automation completed successfully (simulation mode)",
                screenshot_url=screenshot_url,
                container_id=f"mock-container-{session_id[:8]}",
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Mock automation failed for session {session_id}: {str(e)}")
            
            # Update session as failed
            session = self.db.query(AndroidAutomationSession).filter(
                AndroidAutomationSession.session_id == session_id
            ).first()
            if session:
                session.status = AutomationStatus.FAILED
                session.end_time = datetime.utcnow()
                session.error_message = str(e)
                self.db.commit()
            
            return AutomationResponse(
                session_id=session_id,
                status=AutomationStatus.FAILED,
                message=f"Mock automation failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _simulate_container_setup(self, session: AndroidAutomationSession, platform: Platform):
        """Simulate Android container setup"""
        logger.info(f"Simulating container setup for session {session.session_id}")
        time.sleep(2)  # Simulate setup time
        
        # Create mock container record
        container = AndroidContainer(
            container_id=f"mock-container-{session.session_id[:8]}",
            container_name=f"mock-android-{session.session_id[:8]}",
            image_name="budtmo/docker-android:api_30_x86",
            image_tag="api_30_x86",
            status=ContainerStatus.RUNNING,
            host_port=5555,
            container_port=5555,
            started_at=datetime.utcnow()
        )
        
        self.db.add(container)
        self.db.commit()
        self.db.refresh(container)
        
        # Update session with container info
        session.container_id = container.container_id
        session.container_name = container.container_name
        session.status = AutomationStatus.RUNNING
        self.db.commit()
        
        logger.info(f"Mock container {container.container_id} is ready")
    
    def _simulate_apk_download(self, session: AndroidAutomationSession, platform: Platform, apk_url: str):
        """Simulate APK download"""
        logger.info(f"Simulating APK download for session {session.session_id}")
        logger.info(f"Platform: {platform.name} ({platform.display_name})")
        logger.info(f"APK URL: {apk_url}")
        
        # Simulate download time
        time.sleep(3)
        
        # Create mock APK file
        apk_filename = f"{platform.name}_{session.session_id[:8]}.apk"
        apk_path = os.path.join(self.apk_download_dir, apk_filename)
        
        # Create a mock APK file (just a text file for simulation)
        with open(apk_path, 'w') as f:
            f.write(f"Mock APK for {platform.name}\nSession: {session.session_id}\nURL: {apk_url}")
        
        logger.info(f"Mock APK downloaded to {apk_path}")
        
        # Update session
        session.apk_path = apk_path
        self.db.commit()
        
        return apk_path
    
    def _simulate_screenshot_capture(self, session: AndroidAutomationSession, platform: Platform, wait_time: int) -> str:
        """Simulate screenshot capture"""
        logger.info(f"Simulating screenshot capture for session {session.session_id}")
        logger.info(f"Platform: {platform.name} ({platform.display_name})")
        
        # Simulate app launch and wait time
        logger.info(f"Simulating app launch with package: {session.app_package}")
        time.sleep(2)  # Simulate launch time
        
        logger.info(f"Simulating {wait_time} seconds wait for app to load...")
        time.sleep(min(wait_time, 5))  # Cap at 5 seconds for simulation
        
        # Create mock screenshot
        screenshot_filename = f"screenshot_{session.session_id[:8]}.png"
        screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
        
        # Create a mock screenshot file (just a text file for simulation)
        with open(screenshot_path, 'w') as f:
            f.write(f"Mock Screenshot for {platform.name}\nSession: {session.session_id}\nApp: {session.app_package}\nTimestamp: {datetime.utcnow()}")
        
        # Generate public URL
        screenshot_url = f"http://localhost:8000/screenshots/{screenshot_filename}"
        
        logger.info(f"Mock screenshot captured: {screenshot_url}")
        
        # Update session
        session.screenshot_path = screenshot_path
        session.screenshot_url = screenshot_url
        self.db.commit()
        
        return screenshot_url
    
    def get_session_status(self, session_id: str) -> Optional[AndroidAutomationSession]:
        """Get automation session status"""
        return self.db.query(AndroidAutomationSession).filter(
            AndroidAutomationSession.session_id == session_id
        ).first()
    
    def cleanup_session(self, session_id: str) -> bool:
        """Cleanup automation session"""
        session = self.get_session_status(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for cleanup")
            return False
        
        try:
            # Clean up mock files
            if session.apk_path and os.path.exists(session.apk_path):
                os.remove(session.apk_path)
                logger.info(f"Removed mock APK file: {session.apk_path}")
            
            if session.screenshot_path and os.path.exists(session.screenshot_path):
                os.remove(session.screenshot_path)
                logger.info(f"Removed mock screenshot file: {session.screenshot_path}")
            
            # Clean up associated container if exists
            if session.container_id:
                container = self.db.query(AndroidContainer).filter(
                    AndroidContainer.container_id == session.container_id
                ).first()
                
                if container:
                    container.is_active = False
                    container.status = ContainerStatus.STOPPED
                    container.stopped_at = datetime.utcnow()
                    logger.info(f"Deactivated mock container: {session.container_id}")
            
            # Delete the session from database
            self.db.delete(session)
            self.db.commit()
            
            logger.info(f"Successfully cleaned up mock session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup mock session {session_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def list_containers(self) -> List[AndroidContainerResponse]:
        """List all Android containers"""
        containers = self.db.query(AndroidContainer).all()
        return [AndroidContainerResponse.model_validate(container) for container in containers]
    
    def get_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Get mock container resource usage"""
        return {
            "container_id": container_id,
            "cpu_usage": "25.5%",
            "memory_usage": "1.2GB / 4GB",
            "network_usage": "1.5MB / 2.3MB",
            "block_usage": "512KB / 1.2MB",
            "status": "running",
            "mock_mode": True
        }
