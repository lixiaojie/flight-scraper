#!/usr/bin/env python3
"""
iOS iPhone Automation Main Script
Connects to iPhone, launches configured app, and takes screenshots
"""

import os
import time
import subprocess
import logging
import json
from datetime import datetime
from appium import webdriver
from appium.options.ios import XCUITestOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IOSAutomation:
    def __init__(self, screenshots_dir="screenshots/ios"):
        # Use Docker volume path when running inside Docker, otherwise use local path
        if os.path.exists("/app"):
            self.screenshots_dir = "/app/screenshots/ios"
        else:
            self.screenshots_dir = screenshots_dir
        self.ensure_screenshots_dir()
        
    def ensure_screenshots_dir(self):
        """Ensure screenshots directory exists"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def get_iphone_udid(self):
        """Get the UDID of connected iPhone"""
        try:
            # Try different paths for xcrun (host vs Docker)
            xcrun_paths = ["/usr/bin/xcode/xcrun", "xcrun"]
            for xcrun_path in xcrun_paths:
                try:
                    result = subprocess.run(
                        [xcrun_path, "xctrace", "list", "devices"],
                        capture_output=True, text=True, check=True
                    )
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                # If xcrun is not available, use a hardcoded UDID for testing
                logger.warning("xcrun not found, using hardcoded iPhone UDID")
                return "00008140-000A40E811C0801C"  # Your iPhone UDID
            
            devices = []
            in_devices_section = False
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line == "== Devices ==":
                    in_devices_section = True
                    continue
                elif line.startswith("== ") and line.endswith(" =="):
                    in_devices_section = False
                    continue
                if in_devices_section and line and not line.startswith("=="):
                    if '(' in line and ')' in line:
                        parts = line.split('(')
                        name = parts[0].strip()
                        if len(parts) >= 3:
                            udid = parts[2].rstrip(')').strip()
                            if "iPhone" in name:
                                devices.append({"name": name, "udid": udid})
            
            if devices:
                return devices[0]["udid"]
            # Fallback to hardcoded UDID
            logger.warning("No iPhone found in device list, using hardcoded UDID")
            return "00008140-000A40E811C0801C"  # Your iPhone UDID
        except Exception as e:
            logger.error(f"Failed to get iPhone UDID: {e}")
            # Fallback to hardcoded UDID
            logger.warning("Using hardcoded iPhone UDID as fallback")
            return "00008140-000A40E811C0801C"  # Your iPhone UDID
    
    def check_appium_server(self):
        """Check if Appium server is running"""
        try:
            import requests
            # Try host.docker.internal first (when running from Docker), then localhost
            urls = ["http://host.docker.internal:4723/status", "http://localhost:4723/status"]
            for url in urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def connect_to_iphone(self, iphone_udid):
        """Connect to iPhone via Appium"""
        capabilities = dict(
            platformName='iOS',
            automationName='XCUITest',
            deviceName='iPhone',
            udid=iphone_udid,
            xcodeOrgId='3NPZ4D89D6',  # Your Team ID
            xcodeSigningId='Apple Development',
            noReset=True,
            fullReset=False
        )
        
        options = XCUITestOptions().load_capabilities(capabilities)
        # Try host.docker.internal first (when running from Docker), then localhost
        urls = ["http://host.docker.internal:4723", "http://localhost:4723"]
        for url in urls:
            try:
                driver = webdriver.Remote(url, options=options)
                return driver
            except Exception as e:
                logger.warning(f"Failed to connect to {url}: {e}")
                continue
        raise Exception("Could not connect to Appium server on any URL")
    
    def launch_app(self, driver, bundle_id):
        """Launch app by bundle ID"""
        try:
            driver.activate_app(bundle_id)
            time.sleep(3)  # Wait for app to launch
            return True
        except Exception as e:
            logger.error(f"Failed to launch app {bundle_id}: {e}")
            return False
    
    def take_screenshot(self, driver, session_id=None):
        """Take screenshot and save to screenshots directory"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if session_id:
                filename = f"ios_screenshot_{session_id}_{timestamp}.png"
            else:
                filename = f"ios_screenshot_{timestamp}.png"
            
            screenshot_path = os.path.join(self.screenshots_dir, filename)
            driver.save_screenshot(screenshot_path)
            
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                logger.info(f"Screenshot saved: {screenshot_path} ({file_size} bytes)")
                return screenshot_path
            else:
                logger.error("Screenshot file was not created")
                return None
                
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def run_automation(self, platform_config, session_id=None):
        """
        Main automation function
        Args:
            platform_config: Dict with 'bundle_id' key
            session_id: Optional session ID for naming screenshots
        Returns:
            Dict with automation results
        """
        start_time = time.time()
        result = {
            "status": "failed",
            "message": "",
            "screenshot_path": None,
            "execution_time": 0
        }
        
        try:
            # Check Appium server
            if not self.check_appium_server():
                result["message"] = "Appium server is not running"
                return result
            
            # Get iPhone UDID
            iphone_udid = self.get_iphone_udid()
            if not iphone_udid:
                result["message"] = "No iPhone found. Please connect your iPhone via USB."
                return result
            
            logger.info(f"Found iPhone: {iphone_udid}")
            
            # Connect to iPhone
            driver = self.connect_to_iphone(iphone_udid)
            logger.info("Connected to iPhone successfully")
            
            # Launch app
            bundle_id = platform_config.get('bundle_id')
            if not bundle_id:
                result["message"] = "No bundle_id specified in platform config"
                return result
            
            if not self.launch_app(driver, bundle_id):
                result["message"] = f"Failed to launch app: {bundle_id}"
                return result
            
            logger.info(f"Launched app: {bundle_id}")
            
            # Take screenshot
            screenshot_path = self.take_screenshot(driver, session_id)
            if not screenshot_path:
                result["message"] = "Failed to take screenshot"
                return result
            
            # Success
            execution_time = time.time() - start_time
            result.update({
                "status": "completed",
                "message": "iOS automation completed successfully",
                "screenshot_path": screenshot_path,
                "execution_time": execution_time
            })
            
            logger.info("iOS automation completed successfully")
            
        except Exception as e:
            execution_time = time.time() - start_time
            result.update({
                "message": f"iOS automation failed: {str(e)}",
                "execution_time": execution_time
            })
            logger.error(f"iOS automation failed: {e}")
            
        finally:
            # Clean up
            if 'driver' in locals():
                try:
                    driver.quit()
                    logger.info("Driver session closed")
                except Exception as e:
                    logger.warning(f"Error closing driver: {e}")
        
        return result

def main():
    """Main function with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='iOS iPhone Automation')
    parser.add_argument('--platform-config', type=str, required=True,
                       help='Platform configuration as JSON string')
    parser.add_argument('--wait-time', type=int, default=5,
                       help='Wait time in seconds (default: 5)')
    parser.add_argument('--capture-screenshot', type=str, default='true',
                       help='Capture screenshot (default: true)')
    parser.add_argument('--session-id', type=str, default=None,
                       help='Session ID for naming screenshots')
    
    args = parser.parse_args()
    
    try:
        # Parse platform configuration
        platform_config = json.loads(args.platform_config)
        capture_screenshot = args.capture_screenshot.lower() == 'true'
        
        # Run automation
        automation = IOSAutomation()
        result = automation.run_automation(platform_config, args.session_id)
        
        # Output result as JSON for backend integration
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "status": "failed",
            "message": f"iOS automation failed: {str(e)}",
            "screenshot_path": None,
            "execution_time": 0
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
