"""
Database migration script for Android automation tables
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine, SessionLocal

def migrate_android_automation():
    """Create Android automation tables"""

    db = SessionLocal()
    try:
        # Create android_automation_sessions table
        print("Creating android_automation_sessions table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS android_automation_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                platform_id INTEGER NOT NULL REFERENCES platforms(id),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                container_id VARCHAR(100),
                container_name VARCHAR(100),
                app_package VARCHAR(200),
                app_version VARCHAR(50),
                apk_path VARCHAR(500),
                screenshot_path VARCHAR(500),
                screenshot_url VARCHAR(1000),
                start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                end_time TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
                logs TEXT,
                cpu_usage VARCHAR(50),
                memory_usage VARCHAR(50),
                disk_usage VARCHAR(50)
            )
        """))
        print("✅ android_automation_sessions table created")

        # Create android_containers table
        print("Creating android_containers table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS android_containers (
                id SERIAL PRIMARY KEY,
                container_id VARCHAR(100) UNIQUE NOT NULL,
                container_name VARCHAR(100) UNIQUE NOT NULL,
                image_name VARCHAR(200) NOT NULL,
                image_tag VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'stopped',
                is_active BOOLEAN DEFAULT TRUE,
                cpu_limit VARCHAR(50),
                memory_limit VARCHAR(50),
                disk_limit VARCHAR(50),
                host_port INTEGER,
                container_port INTEGER DEFAULT 5555,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                started_at TIMESTAMP WITH TIME ZONE,
                stopped_at TIMESTAMP WITH TIME ZONE
            )
        """))
        print("✅ android_containers table created")

        # Create indexes for better performance
        print("Creating indexes...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_automation_sessions_platform_id ON android_automation_sessions(platform_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_automation_sessions_status ON android_automation_sessions(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_automation_sessions_start_time ON android_automation_sessions(start_time)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_containers_status ON android_containers(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_containers_is_active ON android_containers(is_active)"))
        print("✅ Indexes created")

        db.commit()
        print("🎉 Android automation migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_android_automation()
