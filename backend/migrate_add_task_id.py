#!/usr/bin/env python3
"""
添加task_id字段到flight_results表的迁移脚本
"""

from database_config import DATABASE_URL
from sqlalchemy import create_engine, text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def migrate_add_task_id():
    """添加task_id字段到flight_results表"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # 首先检查表是否存在
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='flight_results'
            """))

            if result.fetchone() is None:
                print("⚠️ flight_results 表不存在，请先运行数据库初始化脚本。")
                return

            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('flight_results')
                WHERE name = 'task_id'
            """))

            if result.fetchone()[0] > 0:
                print("✅ task_id 字段已存在，跳过迁移")
                return

            # 添加task_id字段
            conn.execute(text("""
                ALTER TABLE flight_results
                ADD COLUMN task_id INTEGER
            """))

            # 创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_task_id ON flight_results(task_id)
            """))

            conn.commit()
            print("✅ task_id 字段添加成功")

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")


if __name__ == "__main__":
    migrate_add_task_id()
