#!/usr/bin/env python3
"""
数据库迁移：添加字段来源标识
用于标识哪些字段来自OCR，哪些来自大模型API
"""
from database_config import DATABASE_URL
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_migration():
    """运行数据库迁移"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        print("🔍 检查 flight_results 表结构...")
        inspector = Inspector.from_engine(db.connection())
        if 'flight_results' not in inspector.get_table_names():
            print("⚠️ 表 'flight_results' 不存在，跳过迁移。")
            return

        existing_columns = [col['name']
                            for col in inspector.get_columns('flight_results')]
        print(f"现有列: {existing_columns}")

        if 'field_sources' not in existing_columns:
            print("➕ 添加列: field_sources TEXT")
            db.execute(
                text("ALTER TABLE flight_results ADD COLUMN field_sources TEXT"))
            db.commit()
            print("✅ field_sources 列添加成功")
        else:
            print("跳过添加列: field_sources (已存在)")

        print("✅ 数据库迁移完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("数据库迁移：添加字段来源标识")
    print("=" * 80)
    run_migration()
