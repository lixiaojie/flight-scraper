"""
Android Automation Service for containerized Android app testing
"""

import os
import json
import time
import uuid
import subprocess
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


class AndroidAutomationService:
    """Service for Android automation operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.docker_client = None
        self.screenshots_dir = "/app/screenshots"
        self.apk_download_dir = "/app/downloads"
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.apk_download_dir, exist_ok=True)
    
    def start_automation(self, request: AutomationRequest) -> AutomationResponse:
        """Start Android automation process"""
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
            
            # Use platform settings as primary source, request parameters as overrides
            app_package = request.app_package or platform.bundle_id
            app_version = request.app_version or "latest"
            apk_url = request.apk_url or platform.download_url
            
            logger.info(f"Using platform settings for {platform.name}:")
            logger.info(f"  - App Package: {app_package}")
            logger.info(f"  - App Version: {app_version}")
            logger.info(f"  - APK URL: {apk_url}")
            
            # Create automation session with platform-derived information
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
            
            logger.info(f"Created automation session {session_id}")
            
            # Step 1: Setup Android container
            container = self._setup_android_container(session, platform)
            
            # Step 2: Download and install APK
            apk_path = self._download_and_install_apk(session, platform, apk_url)
            
            # Step 3: Launch app and capture screenshot
            screenshot_url = None
            if request.capture_screenshot:
                screenshot_url = self._launch_app_and_capture_screenshot(
                    session, container, platform, request.wait_time
                )
            
            # Update session as completed
            execution_time = time.time() - start_time
            session.status = AutomationStatus.COMPLETED
            session.end_time = datetime.utcnow()
            session.screenshot_url = screenshot_url
            session.logs = json.dumps({
                "execution_time": execution_time,
                "steps_completed": ["container_setup", "apk_install", "screenshot_capture"],
                "container_id": container.container_id if container else None
            })
            
            self.db.commit()
            
            return AutomationResponse(
                session_id=session_id,
                status=AutomationStatus.COMPLETED,
                message="Automation completed successfully",
                screenshot_url=screenshot_url,
                container_id=container.container_id if container else None,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Automation failed for session {session_id}: {str(e)}")
            
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
                message=f"Automation failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _setup_android_container(self, session: AndroidAutomationSession, platform: Platform) -> AndroidContainer:
        """Setup and start Android container"""
        logger.info(f"Setting up Android container for session {session.session_id}")
        
        # Check if we have an existing container
        existing_container = self.db.query(AndroidContainer).filter(
            AndroidContainer.status == ContainerStatus.RUNNING,
            AndroidContainer.is_active == True
        ).first()
        
        if existing_container:
            logger.info(f"Using existing container {existing_container.container_id}")
            session.container_id = existing_container.container_id
            session.container_name = existing_container.container_name
            self.db.commit()
            return existing_container
        
        # Create new container
        container_name = f"android-automation-{session.session_id[:8]}"
        image_name = "budtmo/docker-android"
        image_tag = "latest"
        
        # Start container using Docker command
        container_id = self._start_docker_container(container_name, image_name, image_tag)
        
        # Create container record
        container = AndroidContainer(
            container_id=container_id,
            container_name=container_name,
            image_name=image_name,
            image_tag=image_tag,
            status=ContainerStatus.RUNNING,
            host_port=5555,  # Default ADB port
            container_port=5555,
            started_at=datetime.utcnow()
        )
        
        self.db.add(container)
        self.db.commit()
        self.db.refresh(container)
        
        # Update session with container info
        session.container_id = container_id
        session.container_name = container_name
        session.status = AutomationStatus.RUNNING
        self.db.commit()
        
        # Wait for container to be ready
        self._wait_for_container_ready(container)
        
        logger.info(f"Android container {container_id} is ready")
        return container
    
    def _start_docker_container(self, container_name: str, image_name: str, image_tag: str) -> str:
        """Start Docker container and return container ID"""
        full_image = f"{image_name}:{image_tag}"
        
        # Pull image if not exists
        pull_cmd = ["docker", "pull", full_image]
        result = subprocess.run(pull_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to pull Docker image: {result.stderr}")
        
        # Start container
        run_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", "5555:5555",  # ADB port
            "-p", "6080:6080",  # VNC port
            "-e", "EMULATOR_DEVICE=Samsung Galaxy S10",
            "-e", "WEB_VNC=true",
            full_image
        ]
        
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to start Docker container: {result.stderr}")
        
        container_id = result.stdout.strip()
        logger.info(f"Started Docker container {container_id}")
        return container_id
    
    def _wait_for_container_ready(self, container: AndroidContainer, timeout: int = 300) -> None:
        """Wait for Android container to be ready"""
        logger.info(f"Waiting for container {container.container_id} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if container is running
            check_cmd = ["docker", "ps", "--filter", f"id={container.container_id}", "--format", "{{.Status}}"]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if "Up" in result.stdout:
                # Wait for Android emulator to fully boot and be available via ADB
                logger.info(f"Container is up, waiting for Android emulator to be ready...")
                for i in range(60):  # Wait up to 5 minutes
                    adb_cmd = ["docker", "exec", container.container_name, "adb", "devices"]
                    adb_result = subprocess.run(adb_cmd, capture_output=True, text=True)
                    if "device" in adb_result.stdout and "List of devices" in adb_result.stdout:
                        logger.info(f"Android emulator is ready after {i*5} seconds")
                        return
                    time.sleep(5)
                
                logger.warning(f"Android emulator may not be fully ready, but proceeding...")
                return
            
            time.sleep(10)
        
        raise Exception(f"Container {container.container_id} did not become ready within {timeout} seconds")
    
    def _download_and_install_apk(self, session: AndroidAutomationSession, platform: Platform, apk_url: str) -> str:
        """Download and install APK into Android container"""
        logger.info(f"Downloading and installing APK for session {session.session_id}")
        logger.info(f"Platform: {platform.name} ({platform.display_name})")
        logger.info(f"APK URL: {apk_url}")
        
        # Use the provided APK URL (already validated in start_automation)
        download_url = apk_url
        
        # Download APK
        apk_filename = f"{platform.name}_{session.session_id[:8]}.apk"
        apk_path = os.path.join(self.apk_download_dir, apk_filename)
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(apk_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded APK to {apk_path}")
        
        # Install APK into container
        install_cmd = [
            "docker", "exec", session.container_name,
            "adb", "install", "-r", f"/tmp/{apk_filename}"
        ]
        
        # Copy APK to container
        copy_cmd = ["docker", "cp", apk_path, f"{session.container_name}:/tmp/{apk_filename}"]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to copy APK to container: {result.stderr}")
        
        # Install APK
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to install APK: {result.stderr}")
        
        logger.info(f"APK installed successfully")
        
        # Update session
        session.apk_path = apk_path
        self.db.commit()
        
        return apk_path
    
    def _launch_app_and_capture_screenshot(self, session: AndroidAutomationSession, container: AndroidContainer, 
                                         platform: Platform, wait_time: int) -> str:
        """Launch app and capture screenshot"""
        logger.info(f"Launching app and capturing screenshot for session {session.session_id}")
        logger.info(f"Platform: {platform.name} ({platform.display_name})")
        
        # Use app package from session (already derived from platform settings)
        app_package = session.app_package
        if not app_package:
            raise ValueError("No app package specified in session")
        
        logger.info(f"Launching app with package: {app_package}")
        
        launch_cmd = [
            "docker", "exec", container.container_name,
            "adb", "shell", "am", "start", "-n", f"{app_package}/.MainActivity"
        ]
        
        result = subprocess.run(launch_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"App launch command failed: {result.stderr}")
        
        # Wait for app to load
        logger.info(f"Waiting {wait_time} seconds for app to load...")
        time.sleep(wait_time)
        
        # Capture screenshot
        screenshot_filename = f"screenshot_{session.session_id[:8]}.png"
        screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
        
        # Take screenshot
        screenshot_cmd = [
            "docker", "exec", container.container_name,
            "adb", "shell", "screencap", "-p", "/tmp/screenshot.png"
        ]
        
        result = subprocess.run(screenshot_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to capture screenshot: {result.stderr}")
        
        # Copy screenshot from container
        copy_cmd = ["docker", "cp", f"{container.container_name}:/tmp/screenshot.png", screenshot_path]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to copy screenshot from container: {result.stderr}")
        
        # Generate public URL (in production, this would be uploaded to cloud storage)
        screenshot_url = f"http://localhost:8000/screenshots/{screenshot_filename}"
        
        logger.info(f"Screenshot captured: {screenshot_url}")
        
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
        """Cleanup automation session and container"""
        session = self.get_session_status(session_id)
        if not session:
            return False
        
        try:
            # Stop and remove container if exists
            if session.container_id:
                stop_cmd = ["docker", "stop", session.container_id]
                subprocess.run(stop_cmd, capture_output=True)
                
                remove_cmd = ["docker", "rm", session.container_id]
                subprocess.run(remove_cmd, capture_output=True)
                
                # Update container status
                container = self.db.query(AndroidContainer).filter(
                    AndroidContainer.container_id == session.container_id
                ).first()
                if container:
                    container.status = ContainerStatus.STOPPED
                    container.stopped_at = datetime.utcnow()
                    self.db.commit()
            
            # Clean up files
            if session.apk_path and os.path.exists(session.apk_path):
                os.remove(session.apk_path)
            
            if session.screenshot_path and os.path.exists(session.screenshot_path):
                os.remove(session.screenshot_path)
            
            logger.info(f"Cleaned up session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {str(e)}")
            return False
    
    def list_containers(self) -> List[AndroidContainerResponse]:
        """List all Android containers"""
        containers = self.db.query(AndroidContainer).all()
        return [AndroidContainerResponse.model_validate(container) for container in containers]
    
    def get_container_resources(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage"""
        stats_cmd = ["docker", "stats", "--no-stream", "--format", "json", container_id]
        result = subprocess.run(stats_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"error": "Failed to get container stats"}
        
        try:
            stats = json.loads(result.stdout.strip())
            return {
                "container_id": container_id,
                "cpu_usage": stats.get("CPUPerc", "0%"),
                "memory_usage": stats.get("MemUsage", "0B / 0B"),
                "network_usage": stats.get("NetIO", "0B / 0B"),
                "block_usage": stats.get("BlockIO", "0B / 0B")
            }
        except json.JSONDecodeError:
            return {"error": "Failed to parse container stats"}
