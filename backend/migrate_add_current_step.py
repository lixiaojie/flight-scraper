#!/usr/bin/env python3
"""
添加 current_step 字段到 task_records 表
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 确保路径正确，以便找到数据库文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DATABASE_URL

def run_migration():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        print("🔍 检查现有表结构...")
        from sqlalchemy.engine.reflection import Inspector
        inspector = Inspector.from_engine(db.connection())
        if 'task_records' not in inspector.get_table_names():
            print("⚠️ 表 'task_records' 不存在，跳过迁移。请确保应用已运行并创建了表。")
            return

        existing_columns = [col['name'] for col in inspector.get_columns('task_records')]
        print(f"现有列: {existing_columns}")

        # 添加 current_step 列
        if 'current_step' not in existing_columns:
            print("➕ 添加列: current_step TEXT")
            db.execute(text("ALTER TABLE task_records ADD COLUMN current_step TEXT DEFAULT '初始化中'"))
        else:
            print("跳过添加列: current_step (已存在)")

        db.commit()
        print("✅ 数据库迁移完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
