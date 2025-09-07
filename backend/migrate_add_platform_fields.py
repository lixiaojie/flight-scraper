#!/usr/bin/env python3
"""
Migration script to add app_name and download_url fields to platforms table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine, SessionLocal

def migrate_platform_fields():
    """Add app_name and download_url columns to platforms table"""
    
    db = SessionLocal()
    try:
        # Check if columns already exist (PostgreSQL syntax)
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'platforms' AND table_schema = 'public'
        """))
        columns = [row[0] for row in result.fetchall()]
        
        if 'app_name' not in columns:
            print("Adding app_name column...")
            db.execute(text("ALTER TABLE platforms ADD COLUMN app_name VARCHAR(200)"))
            print("✅ app_name column added")
        else:
            print("✅ app_name column already exists")
            
        if 'download_url' not in columns:
            print("Adding download_url column...")
            db.execute(text("ALTER TABLE platforms ADD COLUMN download_url VARCHAR(1000)"))
            print("✅ download_url column added")
        else:
            print("✅ download_url column already exists")
        
        db.commit()
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_platform_fields()
