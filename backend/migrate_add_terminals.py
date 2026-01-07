from database_config import DATABASE_URL
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_migration():
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

        if 'departure_terminal' not in existing_columns:
            print("➕ 添加列: departure_terminal TEXT")
            db.execute(
                text("ALTER TABLE flight_results ADD COLUMN departure_terminal TEXT"))
        else:
            print("跳过添加列: departure_terminal (已存在)")

        if 'arrival_terminal' not in existing_columns:
            print("➕ 添加列: arrival_terminal TEXT")
            db.execute(
                text("ALTER TABLE flight_results ADD COLUMN arrival_terminal TEXT"))
        else:
            print("跳过添加列: arrival_terminal (已存在)")

        db.commit()
        print("✅ 数据库迁移完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
