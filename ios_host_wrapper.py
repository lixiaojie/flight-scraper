#!/usr/bin/env python3
"""
Host-based iOS automation wrapper
This script runs on the host and can be called from Docker
"""

import os
import sys
import json
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='iOS Host Automation Wrapper')
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
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(script_dir, 'ios_automation_main.py')
        
        # Check if the main script exists
        if not os.path.exists(main_script):
            raise Exception(f"Main script not found: {main_script}")
        
        # Prepare command to run the main script
        cmd = [
            sys.executable,  # Use the same Python interpreter
            main_script,
            "--platform-config", args.platform_config,
            "--wait-time", str(args.wait_time),
            "--capture-screenshot", args.capture_screenshot
        ]
        
        if args.session_id:
            cmd.extend(["--session-id", args.session_id])
        
        # Run the main script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Script failed: {result.stderr}")
        
        # Output the result
        print(result.stdout)
        
    except Exception as e:
        error_result = {
            "status": "failed",
            "message": f"Host wrapper failed: {str(e)}",
            "screenshot_path": None,
            "execution_time": 0
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
