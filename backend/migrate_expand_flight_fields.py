#!/usr/bin/env python3
"""
扩展航班字段迁移脚本
添加更多航班信息字段
"""

from database_config import DATABASE_URL
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 确保路径正确，以便找到数据库文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_migration():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        print("🔍 检查现有表结构...")

        # 检查 flight_results 表是否存在
        result = db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='flight_results'"))
        if not result.fetchone():
            print("⚠️ 表 'flight_results' 不存在，跳过迁移。请确保应用已运行并创建了表。")
            return

        # 获取现有列
        result = db.execute(text("PRAGMA table_info(flight_results)"))
        existing_columns = [row[1] for row in result.fetchall()]
        print(f"现有列: {existing_columns}")

        # 新增字段列表
        new_columns = [
            ('is_shared_flight', 'TEXT', '是否共享航班'),
            ('aircraft_type', 'TEXT', '飞机型号'),
            ('departure_city', 'TEXT', '出发城市'),
            ('arrival_city', 'TEXT', '到达城市'),
            ('has_stopover', 'TEXT', '是否经停'),
            ('stopover_city', 'TEXT', '经停城市'),
            ('stopover_airport', 'TEXT', '经停机场'),
            ('cabin_class', 'TEXT', '舱位等级'),
            ('discount_rate', 'TEXT', '折扣率'),
            ('original_price', 'REAL', '原价')
        ]

        # 添加新列
        for column_name, column_type, comment in new_columns:
            if column_name not in existing_columns:
                print(f"➕ 添加列: {column_name} {column_type}")
                db.execute(
                    text(
                        f"ALTER TABLE flight_results ADD COLUMN {column_name} {column_type}"))
            else:
                print(f"跳过添加列: {column_name} (已存在)")

        db.commit()
        print("✅ 数据库迁移完成")

    except Exception as e:
        db.rollback()
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
