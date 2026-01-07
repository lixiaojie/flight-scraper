#!/usr/bin/env python3
"""
管理员账号初始化脚本
"""

import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


try:
    from models.admin import Admin
    from models.flight_result import Base
    from models.task_record import TaskRecord
except ImportError:
    # Docker容器中的简化导入
    from models.admin import Admin
    from models.flight_result import Base
    from models.task_record import TaskRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_admin():
    """初始化管理员账号"""
    try:
        # 数据库URL
        from database_config import DATABASE_URL

        # 创建数据库引擎
        engine = create_engine(
            DATABASE_URL, connect_args={
                "check_same_thread": False})

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")

        # 创建会话
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 检查是否已有管理员
        existing_admin = db.query(Admin).filter(
            Admin.username == "admin").first()
        if existing_admin:
            logger.info("✅ 管理员账号已存在")
            return True

        # 创建默认管理员账号
        admin = Admin(
            username="admin",
            email="admin@flight-scraper.com",
            is_superuser=True
        )
        admin.set_password("admin123")  # 默认密码

        db.add(admin)
        db.commit()

        logger.info("✅ 默认管理员账号已创建")
        logger.info("   用户名: admin")
        logger.info("   密码: admin123")
        logger.info("   请及时修改密码！")

        db.close()
        return True

    except Exception as e:
        logger.error(f"❌ 初始化管理员账号失败: {e}")
        return False


def create_custom_admin(
        username: str,
        password: str,
        email: str = None,
        is_superuser: bool = False):
    """创建自定义管理员账号"""
    try:
        from database_config import DATABASE_URL
        engine = create_engine(
            DATABASE_URL, connect_args={
                "check_same_thread": False})
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 检查用户名是否已存在
        existing_admin = db.query(Admin).filter(
            Admin.username == username).first()
        if existing_admin:
            logger.error(f"❌ 用户名 {username} 已存在")
            return False

        # 创建管理员
        admin = Admin(
            username=username,
            email=email,
            is_superuser=is_superuser
        )
        admin.set_password(password)

        db.add(admin)
        db.commit()

        logger.info(f"✅ 管理员账号已创建: {username}")
        db.close()
        return True

    except Exception as e:
        logger.error(f"❌ 创建管理员账号失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 初始化管理员账号...")

    if len(sys.argv) > 1:
        # 创建自定义管理员
        username = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
        email = sys.argv[3] if len(sys.argv) > 3 else None
        is_superuser = sys.argv[4].lower() == "true" if len(
            sys.argv) > 4 else False

        success = create_custom_admin(username, password, email, is_superuser)
    else:
        # 创建默认管理员
        success = init_admin()

    if success:
        print("✅ 管理员账号初始化完成")
    else:
        print("❌ 管理员账号初始化失败")
        sys.exit(1)
