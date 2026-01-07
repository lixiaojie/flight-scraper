"""
添加航空公司字段的数据库迁移脚本
"""

from database_config import DATABASE_URL
from sqlalchemy import create_engine, text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def migrate_add_airline():
    """添加航空公司字段到任务记录表"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # 首先检查表是否存在
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='task_records'
            """))

            if not result.fetchone():
                print("❌ task_records 表不存在，请先运行数据库初始化")
                return

            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('task_records')
                WHERE name = 'airline'
            """))

            if result.fetchone()[0] > 0:
                print("✅ 航空公司字段已存在，跳过迁移")
                return

            # 添加航空公司字段
            conn.execute(text("""
                ALTER TABLE task_records
                ADD COLUMN airline VARCHAR(50) DEFAULT '深圳航空'
            """))

            conn.commit()
            print("✅ 航空公司字段添加成功")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    migrate_add_airline()
