"""
Fix Android automation tables by dropping and recreating them
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine, SessionLocal

def fix_android_automation_tables():
    """Drop and recreate Android automation tables with correct schema"""

    db = SessionLocal()
    try:
        # Drop existing tables
        print("Dropping existing Android automation tables...")
        db.execute(text("DROP TABLE IF EXISTS android_automation_sessions CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS android_containers CASCADE"))
        print("✅ Tables dropped")

        # Create android_containers table first
        print("Creating android_containers table...")
        db.execute(text("""
            CREATE TABLE android_containers (
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

        # Create android_automation_sessions table
        print("Creating android_automation_sessions table...")
        db.execute(text("""
            CREATE TABLE android_automation_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                platform_id INTEGER NOT NULL REFERENCES platforms(id),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                container_id VARCHAR(100),
                container_name VARCHAR(100),
                android_container_id INTEGER REFERENCES android_containers(id),
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

        # Create indexes for better performance
        print("Creating indexes...")
        db.execute(text("CREATE INDEX idx_automation_sessions_platform_id ON android_automation_sessions(platform_id)"))
        db.execute(text("CREATE INDEX idx_automation_sessions_status ON android_automation_sessions(status)"))
        db.execute(text("CREATE INDEX idx_automation_sessions_start_time ON android_automation_sessions(start_time)"))
        db.execute(text("CREATE INDEX idx_containers_status ON android_containers(status)"))
        db.execute(text("CREATE INDEX idx_containers_is_active ON android_containers(is_active)"))
        print("✅ Indexes created")

        db.commit()
        print("🎉 Android automation tables fixed successfully!")

    except Exception as e:
        print(f"❌ Fix failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_android_automation_tables()
