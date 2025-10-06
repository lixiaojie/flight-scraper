#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
try:
    from backend.models.flight_result import Base, FlightResult
    from backend.models.task_record import TaskRecord
    from backend.models.admin import Admin
except ImportError:
    # Docker容器中的简化导入
    from models.flight_result import Base, FlightResult
    from models.task_record import TaskRecord
    from models.admin import Admin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库"""
    try:
        # 数据库URL
        DATABASE_URL = "sqlite:///./flight_scraper.db"
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")
        
        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 检查表是否存在
        tables_to_check = ['flight_results', 'task_records', 'admins']
        for table_name in tables_to_check:
            result = db.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            if result.fetchone():
                logger.info(f"✅ {table_name} 表已存在")
            else:
                logger.error(f"❌ {table_name} 表创建失败")
                return False
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        DATABASE_URL = "sqlite:///./flight_scraper.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 测试查询
        flight_count = db.execute(text("SELECT COUNT(*) FROM flight_results")).fetchone()[0]
        task_count = db.execute(text("SELECT COUNT(*) FROM task_records")).fetchone()[0]
        logger.info(f"✅ 数据库连接成功，当前有 {flight_count} 条航班记录，{task_count} 条任务记录")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 初始化数据库...")
    
    if init_database():
        print("✅ 数据库初始化完成")
        
        if test_database_connection():
            print("✅ 数据库连接测试通过")
        else:
            print("❌ 数据库连接测试失败")
    else:
        print("❌ 数据库初始化失败")
        sys.exit(1)
