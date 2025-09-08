import os
import time
import json
import logging
import subprocess
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from appium import webdriver
from appium.options.ios import XCUITestOptions
from app.models.platform import Platform
from app.models.ios_automation import IOSAutomationSession, IOSContainer, AutomationStatus, ContainerStatus

logger = logging.getLogger(__name__)

class AppiumIOSService:
    def __init__(self, db: Session):
        self.db = db
        self.screenshots_dir = "/app/screenshots"
        self.downloads_dir = "/app/downloads"
        self.appium_server_url = "http://host.docker.internal:4723"
        
        # Ensure directories exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def start_automation(self, platform_id: int, wait_time: int = 10, capture_screenshot: bool = True) -> Dict[str, Any]:
        """Start iOS automation session using Appium"""
        logger.info(f"Starting Appium iOS automation for platform {platform_id}")
        
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
        
        driver = None
        try:
            # Start Appium server if not running
            self._ensure_appium_server_running()
            
            # Get or create iOS container (simulator)
            container = self._get_or_create_container(session)
            
            # Create Appium driver
            driver = self._create_driver(container.container_id, platform)
            
            # Launch the app
            self._launch_app(driver, platform)
            
            # Wait for app to load
            if wait_time > 0:
                logger.info(f"Waiting {wait_time} seconds for app to load...")
                time.sleep(wait_time)
            
            # Capture screenshot if requested
            screenshot_url = None
            if capture_screenshot:
                screenshot_url = self._capture_screenshot(driver, container)
            
            # Update session status
            session.status = AutomationStatus.COMPLETED
            session.screenshot_url = screenshot_url
            session.container_id = container.container_id
            self.db.commit()
            
            logger.info(f"Appium iOS automation completed for session {session.session_id}")
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "message": "Appium iOS automation completed successfully",
                "screenshot_url": screenshot_url,
                "container_id": container.container_id,
                "logs": "Appium iOS automation completed successfully",
                "execution_time": time.time() - session.created_at.timestamp()
            }
            
        except Exception as e:
            logger.error(f"Appium iOS automation failed for session {session.session_id}: {str(e)}")
            session.status = AutomationStatus.FAILED
            self.db.commit()
            
            return {
                "session_id": session.session_id,
                "status": "failed",
                "message": f"Appium iOS automation failed: {str(e)}",
                "screenshot_url": None,
                "container_id": None,
                "logs": f"Error: {str(e)}",
                "execution_time": time.time() - session.created_at.timestamp()
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Failed to quit driver: {str(e)}")
    
    def _ensure_appium_server_running(self) -> None:
        """Ensure Appium server is running (connecting to host server)"""
        try:
            # Check if Appium server is accessible
            import requests
            response = requests.get(f"{self.appium_server_url}/status", timeout=5)
            if response.status_code == 200:
                logger.info("Appium server is accessible on host")
                return
        except Exception as e:
            logger.error(f"Failed to connect to Appium server: {e}")
            raise Exception(f"Failed to connect to Appium server on host: {e}")
    
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
    
    def _create_driver(self, device_id: str, platform: Platform) -> webdriver.Remote:
        """Create Appium driver for iOS"""
        options = XCUITestOptions()
        
        # Basic iOS capabilities
        options.platform_name = "iOS"
        options.platform_version = "18.0"  # Adjust based on your simulator
        options.device_name = "iPhone 16 Pro"
        options.udid = device_id
        
        # App capabilities
        if platform.bundle_id:
            options.bundle_id = platform.bundle_id
        
        # Automation capabilities
        options.automation_name = "XCUITest"
        options.no_reset = True
        options.full_reset = False
        
        # Additional capabilities
        options.new_command_timeout = 300
        options.command_timeouts = {"implicit": 30}
        
        logger.info(f"Creating Appium driver for device {device_id}")
        logger.info(f"Platform: {platform.name} (Bundle ID: {platform.bundle_id})")
        
        driver = webdriver.Remote(
            command_executor=self.appium_server_url,
            options=options
        )
        
        return driver
    
    def _launch_app(self, driver: webdriver.Remote, platform: Platform) -> None:
        """Launch the app on the device"""
        try:
            if platform.bundle_id:
                logger.info(f"Launching app with bundle ID: {platform.bundle_id}")
                driver.activate_app(platform.bundle_id)
            else:
                logger.info("No bundle ID specified, using current app")
            
            # Wait for app to load
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"Failed to launch app: {str(e)}")
            # Continue anyway, app might already be running
    
    def _capture_screenshot(self, driver: webdriver.Remote, container: IOSContainer) -> str:
        """Capture screenshot using Appium"""
        try:
            screenshot_filename = f"appium_ios_screenshot_{container.container_id}_{int(time.time())}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            # Take screenshot using Appium
            screenshot_base64 = driver.get_screenshot_as_base64()
            
            # Save screenshot
            import base64
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_base64))
            
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
