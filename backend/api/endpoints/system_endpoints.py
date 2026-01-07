"""
系统控制API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import subprocess
import requests
import os

from core.database import get_db
from models.admin import Admin
from api.endpoints.admin_endpoints import get_current_admin

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    """获取系统状态"""
    try:
        status = {
            "web": "running",
            "frontend": "running",
            "appium": "unknown",
            "android": "unknown"
        }

        # 检查Appium服务
        try:
            response = requests.get("http://localhost:4723/status", timeout=5)
            status["appium"] = "running" if response.status_code == 200 else "stopped"
        except BaseException:
            status["appium"] = "stopped"

        # 检查Android设备
        try:
            result = subprocess.run(
                ["adb", "devices"], capture_output=True, text=True, timeout=5)
            if "device" in result.stdout:
                status["android"] = "running"
            else:
                status["android"] = "stopped"
        except BaseException:
            status["android"] = "unknown"

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_system(current_admin: Admin = Depends(get_current_admin)):
    """启动系统服务"""
    try:
        # 启动Docker Compose服务
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"message": "系统启动成功", "output": result.stdout}
        else:
            return {"message": "系统启动失败", "error": result.stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_system(current_admin: Admin = Depends(get_current_admin)):
    """停止系统服务"""
    try:
        # 停止Docker Compose服务
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"message": "系统停止成功", "output": result.stdout}
        else:
            return {"message": "系统停止失败", "error": result.stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scraper/run")
async def run_scraper(current_admin: Admin = Depends(get_current_admin)):
    """运行抓取任务"""
    try:
        # 运行抓取脚本
        result = subprocess.run(
            ["python3", "scripts/enhanced_flight_scraper.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"message": "抓取任务启动成功", "output": result.stdout}
        else:
            return {"message": "抓取任务启动失败", "error": result.stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_system_logs(current_admin: Admin = Depends(get_current_admin)):
    """获取系统日志"""
    try:
        # 获取Docker Compose日志
        result = subprocess.run(
            ["docker-compose", "logs", "--tail=100"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            capture_output=True,
            text=True
        )

        return {"logs": result.stdout}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
