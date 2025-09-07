#!/usr/bin/env python3
"""
Script to add the initial 12306 platform configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.platform import Platform, PlatformType

def add_12306_platform():
    """Add the 12306 platform configuration"""
    
    db = SessionLocal()
    try:
        # Check if 12306 platform already exists
        existing_platform = db.query(Platform).filter(Platform.name == '12306').first()
        
        if existing_platform:
            print("✅ 12306 platform already exists")
            print(f"   ID: {existing_platform.id}")
            print(f"   Name: {existing_platform.name}")
            print(f"   Bundle ID: {existing_platform.bundle_id}")
            print(f"   App Name: {existing_platform.app_name}")
            print(f"   Download URL: {existing_platform.download_url}")
            return
        
        # Create new 12306 platform
        platform = Platform(
            name='12306',
            display_name='12306 Railway',
            platform_type=PlatformType.MOBILE_APP,
            bundle_id='com.chinarailway.globalticketing',
            app_name='12306',
            download_url='https://dynamic.12306.cn/otn/appdownload/12306v5.9.4.5.apk',
            is_active=True
        )
        
        db.add(platform)
        db.commit()
        db.refresh(platform)
        
        print("🎉 12306 platform added successfully!")
        print(f"   ID: {platform.id}")
        print(f"   Name: {platform.name}")
        print(f"   Display Name: {platform.display_name}")
        print(f"   Platform Type: {platform.platform_type}")
        print(f"   Bundle ID: {platform.bundle_id}")
        print(f"   App Name: {platform.app_name}")
        print(f"   Download URL: {platform.download_url}")
        print(f"   Active: {platform.is_active}")
        
    except Exception as e:
        print(f"❌ Failed to add 12306 platform: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_12306_platform()
