"""
管理员服务
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from models.admin import Admin
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_admin(
            self,
            username: str,
            password: str,
            email: str = None,
            is_superuser: bool = False) -> Admin:
        """创建管理员账号"""
        try:
            # 检查用户名是否已存在
            existing_admin = self.db.query(Admin).filter(
                Admin.username == username).first()
            if existing_admin:
                raise ValueError(f"用户名 {username} 已存在")

            # 创建新管理员
            admin = Admin(
                username=username,
                email=email,
                is_superuser=is_superuser
            )
            admin.set_password(password)

            self.db.add(admin)
            self.db.commit()
            self.db.refresh(admin)

            logger.info(f"管理员账号已创建: {username}")
            return admin

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建管理员账号失败: {e}")
            raise e

    def authenticate(self, username: str, password: str) -> Optional[Admin]:
        """验证管理员登录"""
        try:
            admin = self.db.query(Admin).filter(
                Admin.username == username,
                Admin.is_active
            ).first()

            if admin and admin.check_password(password):
                # 更新最后登录时间
                admin.last_login = datetime.now()
                self.db.commit()
                logger.info(f"管理员登录成功: {username}")
                return admin
            else:
                logger.warning(f"管理员登录失败: {username}")
                return None

        except Exception as e:
            logger.error(f"验证管理员登录失败: {e}")
            return None

    def get_admin_by_username(self, username: str) -> Optional[Admin]:
        """根据用户名获取管理员"""
        try:
            return self.db.query(Admin).filter(
                Admin.username == username).first()
        except Exception as e:
            logger.error(f"获取管理员信息失败: {e}")
            return None

    def get_admin_by_id(self, admin_id: int) -> Optional[Admin]:
        """根据ID获取管理员"""
        try:
            return self.db.query(Admin).filter(Admin.id == admin_id).first()
        except Exception as e:
            logger.error(f"获取管理员信息失败: {e}")
            return None

    def update_password(self, admin_id: int, new_password: str) -> bool:
        """更新管理员密码"""
        try:
            admin = self.get_admin_by_id(admin_id)
            if not admin:
                return False

            admin.set_password(new_password)
            self.db.commit()

            logger.info(f"管理员密码已更新: {admin.username}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新管理员密码失败: {e}")
            return False

    def deactivate_admin(self, admin_id: int) -> bool:
        """停用管理员账号"""
        try:
            admin = self.get_admin_by_id(admin_id)
            if not admin:
                return False

            admin.is_active = False
            self.db.commit()

            logger.info(f"管理员账号已停用: {admin.username}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"停用管理员账号失败: {e}")
            return False

    def activate_admin(self, admin_id: int) -> bool:
        """激活管理员账号"""
        try:
            admin = self.get_admin_by_id(admin_id)
            if not admin:
                return False

            admin.is_active = True
            self.db.commit()

            logger.info(f"管理员账号已激活: {admin.username}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"激活管理员账号失败: {e}")
            return False
