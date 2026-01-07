"""
管理员API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import jwt

from core.database import get_db
from services.admin_service import AdminService
from models.admin import Admin
from schemas.admin_schema import AdminLoginRequest, AdminResponse, AdminCreateRequest
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


def create_access_token(data: dict):
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_admin(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)):
    """获取当前管理员"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_service = AdminService(db)
    admin = admin_service.get_admin_by_username(username)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin


@router.post("/login")
async def admin_login(
        request: AdminLoginRequest,
        db: Session = Depends(get_db)):
    """管理员登录"""
    try:
        admin_service = AdminService(db)
        admin = admin_service.authenticate(request.username, request.password)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        access_token = create_access_token(data={"sub": admin.username})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "admin": admin.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_admin(
        request: AdminCreateRequest,
        current_admin: Admin = Depends(get_current_admin),
        db: Session = Depends(get_db)):
    """创建管理员账号（需要超级管理员权限）"""
    try:
        if not current_admin.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要超级管理员权限"
            )

        admin_service = AdminService(db)
        admin = admin_service.create_admin(
            username=request.username,
            password=request.password,
            email=request.email,
            is_superuser=request.is_superuser
        )

        return {"message": "管理员账号创建成功", "admin": admin.to_dict()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(
        current_admin: Admin = Depends(get_current_admin)):
    """获取当前管理员信息"""
    return current_admin.to_dict()


@router.put("/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        if not current_admin.check_password(old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )

        admin_service = AdminService(db)
        success = admin_service.update_password(current_admin.id, new_password)

        if success:
            return {"message": "密码修改成功"}
        else:
            raise HTTPException(status_code=500, detail="密码修改失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
