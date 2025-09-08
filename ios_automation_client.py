#!/usr/bin/env python3
"""
iOS Automation Client - Runs on host system to interact with iOS Simulator
"""

import os
import time
import subprocess
import json
import logging
import argparse
import sys
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IOSAutomationClient:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.screenshots_dir = os.path.expanduser("~/Desktop/ios_screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def start_automation(self, platform_id: int, wait_time: int = 5, capture_screenshot: bool = True) -> Dict[str, Any]:
        """Start iOS automation session"""
        start_time = time.time()
        logger.info(f"Starting iOS automation for platform {platform_id}")
        
        try:
            # Get platform information from backend
            platform = self._get_platform_info(platform_id)
            if not platform:
                raise Exception(f"Platform {platform_id} not found")
            
            # Start iOS simulator
            device_id = self._start_simulator()
            
            # Download and install app (simulated)
            if platform.get("download_url"):
                self._simulate_app_installation(platform)
            
            # Wait for app to load
            if wait_time > 0:
                logger.info(f"Waiting {wait_time} seconds for app to load...")
                time.sleep(wait_time)
            
            # Capture screenshot if requested
            screenshot_url = None
            if capture_screenshot:
                screenshot_url = self._capture_screenshot(device_id)
            
            execution_time = time.time() - start_time
            logger.info("iOS automation completed successfully")
            
            return {
                "status": "completed",
                "message": "iOS automation completed successfully",
                "screenshot_url": screenshot_url,
                "device_id": device_id,
                "platform": platform,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"iOS automation failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"iOS automation failed: {str(e)}",
                "screenshot_url": None,
                "device_id": None,
                "platform": None,
                "execution_time": execution_time
            }
    
    def _get_platform_info(self, platform_id: int) -> Optional[Dict[str, Any]]:
        """Get platform information (simulated for demo)"""
        # For demo purposes, return a mock platform
        return {
            "id": platform_id,
            "name": "12306",
            "display_name": "12306 Railway",
            "platform_type": "mobile_app",
            "download_url": "https://apps.apple.com/app/12306/id564818797"
        }
    
    def _start_simulator(self) -> str:
        """Start iOS simulator and return device ID"""
        try:
            # List available simulators
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "--json"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to list simulators: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Find iPhone 16 Pro simulator
            device_id = None
            for runtime, devices in data["devices"].items():
                if "iOS" in runtime:
                    for device in devices:
                        if "iPhone 16 Pro" in device["name"]:
                            device_id = device["udid"]
                            break
                    if device_id:
                        break
            
            if not device_id:
                raise Exception("No iPhone 16 Pro simulator found")
            
            # Boot the simulator (if not already booted)
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
            return device_id
            
        except Exception as e:
            logger.error(f"Failed to start simulator: {str(e)}")
            raise
    
    def _simulate_app_installation(self, platform: Dict[str, Any]) -> None:
        """Simulate iOS app installation"""
        logger.info(f"Simulating installation of {platform['name']} app")
        logger.info(f"App URL: {platform.get('download_url', 'N/A')}")
        logger.info("Note: Real iOS app installation would require .ipa file and proper provisioning")
    
    def _capture_screenshot(self, device_id: str) -> str:
        """Capture screenshot from iOS simulator"""
        try:
            screenshot_filename = f"ios_screenshot_{device_id}_{int(time.time())}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            
            # Take screenshot using simctl
            result = subprocess.run(
                ["xcrun", "simctl", "io", device_id, "screenshot", screenshot_path],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to capture screenshot: {result.stderr}")
            
            logger.info(f"Screenshot captured: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise
    
    def list_simulators(self) -> Dict[str, Any]:
        """List available iOS simulators"""
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "--json"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to list simulators: {result.stderr}")
            
            return json.loads(result.stdout)
            
        except Exception as e:
            logger.error(f"Failed to list simulators: {str(e)}")
            raise
    
    def extract_app_data(self, device_id: str, bundle_id: str) -> Dict[str, Any]:
        """Extract data from iOS app"""
        try:
            # Get app container path
            result = subprocess.run(
                ["xcrun", "simctl", "get_app_container", device_id, bundle_id, "data"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to get app container: {result.stderr}")
            
            container_path = result.stdout.strip()
            logger.info(f"App container path: {container_path}")
            
            # List app data contents
            if os.path.exists(container_path):
                app_data = {
                    "container_path": container_path,
                    "documents": [],
                    "library": [],
                    "tmp": []
                }
                
                # List Documents directory
                docs_path = os.path.join(container_path, "Documents")
                if os.path.exists(docs_path):
                    app_data["documents"] = os.listdir(docs_path)
                
                # List Library directory
                lib_path = os.path.join(container_path, "Library")
                if os.path.exists(lib_path):
                    app_data["library"] = os.listdir(lib_path)
                
                # List tmp directory
                tmp_path = os.path.join(container_path, "tmp")
                if os.path.exists(tmp_path):
                    app_data["tmp"] = os.listdir(tmp_path)
                
                return app_data
            else:
                return {"error": "App container not found"}
                
        except Exception as e:
            logger.error(f"Failed to extract app data: {str(e)}")
            raise

def main():
    """Main function for testing and CLI usage"""
    parser = argparse.ArgumentParser(description="iOS Automation Client")
    parser.add_argument("--platform-id", type=int, help="Platform ID to automate")
    parser.add_argument("--wait-time", type=int, default=5, help="Wait time in seconds")
    parser.add_argument("--capture-screenshot", type=str, default="true", help="Capture screenshot (true/false)")
    parser.add_argument("--list-simulators", action="store_true", help="List available simulators")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    client = IOSAutomationClient()
    
    # If JSON output requested, suppress logging
    if args.json:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        if args.list_simulators:
            # List simulators
            simulators = client.list_simulators()
            if args.json:
                print(json.dumps(simulators, indent=2))
            else:
                print("📱 Available iOS Simulators:")
                for runtime, devices in simulators["devices"].items():
                    if "iOS" in runtime:
                        print(f"\n{runtime}:")
                        for device in devices:
                            status = "🟢 Running" if device["state"] == "Booted" else "🔴 Shutdown"
                            print(f"  - {device['name']} ({device['udid'][:8]}...) {status}")
        elif args.platform_id:
            # Start automation
            capture_screenshot = args.capture_screenshot.lower() == "true"
            result = client.start_automation(
                platform_id=args.platform_id,
                wait_time=args.wait_time,
                capture_screenshot=capture_screenshot
            )
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Status: {result['status']}")
                print(f"Message: {result['message']}")
                if result.get('screenshot_url'):
                    print(f"Screenshot: {result['screenshot_url']}")
        else:
            # Interactive mode
            print("🧪 Testing iOS Automation Client")
            print("=" * 40)
            
            # Test 1: List simulators
            print("\n📱 Available iOS Simulators:")
            try:
                simulators = client.list_simulators()
                for runtime, devices in simulators["devices"].items():
                    if "iOS" in runtime:
                        print(f"\n{runtime}:")
                        for device in devices:
                            status = "🟢 Running" if device["state"] == "Booted" else "🔴 Shutdown"
                            print(f"  - {device['name']} ({device['udid'][:8]}...) {status}")
            except Exception as e:
                print(f"❌ Failed to list simulators: {e}")
            
            # Test 2: Start automation
            print("\n🚀 Starting iOS Automation:")
            try:
                result = client.start_automation(platform_id=1, wait_time=5, capture_screenshot=True)
                print(f"Status: {result['status']}")
                print(f"Message: {result['message']}")
                if result.get('screenshot_url'):
                    print(f"Screenshot: {result['screenshot_url']}")
            except Exception as e:
                print(f"❌ Failed to start automation: {e}")
            
            # Test 3: Extract app data (example)
            print("\n📊 App Data Extraction Example:")
            try:
                # This would work with a real app installed
                print("Note: App data extraction requires a real app to be installed")
                print("Example command: xcrun simctl get_app_container <device_id> <bundle_id> data")
            except Exception as e:
                print(f"❌ Failed to extract app data: {e}")
                
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "screenshot_url": None,
            "device_id": None,
            "platform": None,
            "execution_time": 0
        }
        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
