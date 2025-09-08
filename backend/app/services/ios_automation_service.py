import os
import time
import subprocess
import logging
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.platform import Platform
from app.models.ios_automation import IOSAutomationSession, IOSContainer, AutomationStatus, ContainerStatus

logger = logging.getLogger(__name__)

class IOSAutomationService:
    def __init__(self, db: Session):
        self.db = db
        self.screenshots_dir = "/app/screenshots"
        self.downloads_dir = "/app/downloads"
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def start_automation(self, platform_id: int, wait_time: int = 10, capture_screenshot: bool = True) -> Dict[str, Any]:
        """Start iOS automation session"""
        logger.info(f"Starting iOS automation for platform {platform_id}")
        
        # Get platform information
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            raise Exception(f"Platform {platform_id} not found")
        
        if platform.platform_type != "mobile_app":
            raise Exception(f"Platform {platform.name} is not a mobile app")
        
        # Create automation session
        session = IOSAutomationSession(
            platform_id=platform_id,
            status=AutomationStatus.RUNNING,
            wait_time=wait_time,
            capture_screenshot=capture_screenshot
        )
        self.db.add(session)
        self.db.commit()
        
        try:
            # Get or create iOS container (simulator)
            container = self._get_or_create_container(session)
            
            # Download and install app
            if platform.download_url:
                self._download_and_install_app(session, platform, platform.download_url)
            
            # Wait for app to load
            if wait_time > 0:
                logger.info(f"Waiting {wait_time} seconds for app to load...")
                time.sleep(wait_time)
            
            # Capture screenshot if requested
            screenshot_url = None
            if capture_screenshot:
                screenshot_url = self._capture_screenshot(container)
            
            # Update session status
            session.status = AutomationStatus.COMPLETED
            session.screenshot_url = screenshot_url
            session.container_id = container.container_id
            self.db.commit()
            
            logger.info(f"iOS automation completed for session {session.session_id}")
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "message": "iOS automation completed successfully",
                "screenshot_url": screenshot_url,
                "container_id": container.container_id,
                "logs": "iOS automation completed successfully",
                "execution_time": time.time() - session.created_at.timestamp()
            }
            
        except Exception as e:
            logger.error(f"iOS automation failed for session {session.session_id}: {str(e)}")
            session.status = AutomationStatus.FAILED
            self.db.commit()
            
            return {
                "session_id": session.session_id,
                "status": "failed",
                "message": f"iOS automation failed: {str(e)}",
                "screenshot_url": None,
                "container_id": None,
                "logs": f"Error: {str(e)}",
                "execution_time": time.time() - session.created_at.timestamp()
            }
    
    def _get_or_create_container(self, session: IOSAutomationSession) -> IOSContainer:
        """Get or create iOS simulator container"""
        # Check if there's an existing running simulator
        existing_container = self.db.query(IOSContainer).filter(
            IOSContainer.status == ContainerStatus.RUNNING
        ).first()
        
        if existing_container:
            logger.info(f"Using existing iOS container {existing_container.container_id}")
            session.container_id = existing_container.container_id
            session.container_name = existing_container.container_name
            self.db.commit()
            return existing_container
        
        # Create new container (simulator)
        container_name = f"ios-simulator-{session.session_id[:8]}"
        device_id = self._get_available_simulator()
        
        # Start simulator
        self._start_simulator(device_id)
        
        # Create container record
        container = IOSContainer(
            container_id=device_id,
            container_name=container_name,
            device_type="iPhone 16 Pro",
            status=ContainerStatus.RUNNING,
            is_active=True
        )
        self.db.add(container)
        self.db.commit()
        
        session.container_id = container.container_id
        session.container_name = container.container_name
        session.status = AutomationStatus.RUNNING
        self.db.commit()
        
        logger.info(f"Created iOS container {container.container_id}")
        return container
    
    def _get_available_simulator(self) -> str:
        """Get available iOS simulator device ID"""
        try:
            # List available simulators
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "--json"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to list simulators: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Find iPhone 16 Pro simulator (prefer already booted)
            device_id = None
            for runtime, devices in data["devices"].items():
                if "iOS" in runtime:
                    for device in devices:
                        if "iPhone 16 Pro" in device["name"]:
                            if device["state"] == "Booted":
                                logger.info(f"Found already booted simulator: {device['name']} ({device['udid']})")
                                return device["udid"]
                            elif device["state"] == "Shutdown" and device_id is None:
                                device_id = device["udid"]
                                logger.info(f"Found shutdown simulator: {device['name']} ({device['udid']})")
            
            if device_id:
                return device_id
            
            raise Exception("No iPhone 16 Pro simulator found")
            
        except Exception as e:
            logger.error(f"Failed to get available simulator: {str(e)}")
            raise
    
    def _start_simulator(self, device_id: str) -> None:
        """Start iOS simulator"""
        try:
            # Check if simulator is already booted
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "--json"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for runtime, devices in data["devices"].items():
                    for device in devices:
                        if device["udid"] == device_id and device["state"] == "Booted":
                            logger.info(f"Simulator {device_id} is already booted")
                            # Open Simulator app
                            subprocess.run(["open", "-a", "Simulator"], check=False)
                            return
            
            # Boot the simulator
            result = subprocess.run(
                ["xcrun", "simctl", "boot", device_id],
                capture_output=True, text=True
            )
            
            if result.returncode != 0 and "Booted" not in result.stderr:
                raise Exception(f"Failed to boot simulator: {result.stderr}")
            
            # Open Simulator app
            subprocess.run(["open", "-a", "Simulator"], check=False)
            
            # Wait for simulator to be ready
            time.sleep(10)
            
            logger.info(f"iOS simulator {device_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start simulator: {str(e)}")
            raise
    
    def _download_and_install_app(self, session: IOSAutomationSession, platform: Platform, app_url: str) -> str:
        """Download and install iOS app"""
        logger.info(f"Downloading and installing iOS app for session {session.session_id}")
        logger.info(f"Platform: {platform.name} ({platform.display_name})")
        logger.info(f"App URL: {app_url}")
        
        # For iOS, we'll simulate app installation since we can't install arbitrary apps
        # In a real implementation, you would:
        # 1. Download the .ipa file
        # 2. Install it using xcrun simctl install
        # 3. Launch the app
        
        logger.info("iOS app installation simulated (real implementation would install .ipa file)")
        return "simulated"
    
    def _capture_screenshot(self, container: IOSContainer) -> str:
        """Capture screenshot from iOS simulator"""
        try:
            screenshot_filename = f"ios_screenshot_{container.container_id}_{int(time.time())}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            # Take screenshot using simctl
            result = subprocess.run(
                ["xcrun", "simctl", "io", container.container_id, "screenshot", screenshot_path],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to capture screenshot: {result.stderr}")
            
            # Generate public URL (in production, this would be uploaded to cloud storage)
            screenshot_url = f"http://localhost:8000/screenshots/{screenshot_filename}"
            
            logger.info(f"Screenshot captured: {screenshot_url}")
            return screenshot_url
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all iOS automation sessions"""
        sessions = self.db.query(IOSAutomationSession).all()
        return [
            {
                "session_id": session.session_id,
                "platform_id": session.platform_id,
                "status": session.status,
                "container_id": session.container_id,
                "screenshot_url": session.screenshot_url,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            }
            for session in sessions
        ]
    
    def get_containers(self) -> List[Dict[str, Any]]:
        """Get all iOS containers"""
        containers = self.db.query(IOSContainer).all()
        return [
            {
                "container_id": container.container_id,
                "container_name": container.container_name,
                "device_type": container.device_type,
                "status": container.status,
                "is_active": container.is_active,
                "created_at": container.created_at.isoformat(),
                "started_at": container.started_at.isoformat() if container.started_at else None,
                "stopped_at": container.stopped_at.isoformat() if container.stopped_at else None
            }
            for container in containers
        ]
    
    def stop_container(self, container_id: str) -> Dict[str, str]:
        """Stop iOS simulator container"""
        try:
            # Shutdown simulator
            result = subprocess.run(
                ["xcrun", "simctl", "shutdown", container_id],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to shutdown simulator: {result.stderr}")
            
            # Update container status
            container = self.db.query(IOSContainer).filter(
                IOSContainer.container_id == container_id
            ).first()
            
            if container:
                container.status = ContainerStatus.STOPPED
                container.stopped_at = time.time()
                self.db.commit()
            
            logger.info(f"iOS simulator {container_id} stopped successfully")
            return {"message": f"iOS simulator {container_id} stopped successfully"}
            
        except Exception as e:
            logger.error(f"Failed to stop iOS simulator: {str(e)}")
            raise Exception(f"Failed to stop iOS simulator: {str(e)}")
    
    def start_container(self, container_id: str) -> Dict[str, str]:
        """Start iOS simulator container"""
        try:
            # Boot simulator
            result = subprocess.run(
                ["xcrun", "simctl", "boot", container_id],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to boot simulator: {result.stderr}")
            
            # Open Simulator app
            subprocess.run(["open", "-a", "Simulator"], check=False)
            
            # Update container status
            container = self.db.query(IOSContainer).filter(
                IOSContainer.container_id == container_id
            ).first()
            
            if container:
                container.status = ContainerStatus.RUNNING
                container.started_at = time.time()
                self.db.commit()
            
            logger.info(f"iOS simulator {container_id} started successfully")
            return {"message": f"iOS simulator {container_id} started successfully"}
            
        except Exception as e:
            logger.error(f"Failed to start iOS simulator: {str(e)}")
            raise Exception(f"Failed to start iOS simulator: {str(e)}")
