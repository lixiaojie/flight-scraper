"""
FastAPI主应用
"""

import sys
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
import os
os.environ['TZ'] = 'Asia/Shanghai'
try:
    import time
    time.tzset()
except AttributeError:
    pass


# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from core.database import get_db
    from models.flight_result import FlightResult
    from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
    from api.endpoints.task_endpoints import router as task_router
    from api.endpoints.admin_endpoints import router as admin_router
    from api.endpoints.system_endpoints import router as system_router
    HAS_ROUTERS = True
    print("✅ 路由导入成功")
except ImportError as e:
    # Docker容器中的简化导入
    print(f"❌ 路由导入失败: {e}")
    from core.database import get_db
    from models.flight_result import FlightResult
    from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
    HAS_ROUTERS = False

# 创建FastAPI应用
app = FastAPI(
    title="航班信息API",
    description="12306航班信息抓取和查询API",
    version="1.0.0"
)


@app.on_event("startup")
def _startup_schedule_runner():
    """启动定时/循环任务调度线程，使定时任务到点能执行"""
    try:
        import threading
        from services.schedule_runner import _run_schedule_loop
        t = threading.Thread(target=_run_schedule_loop, daemon=True, name="ScheduleRunner")
        t.start()
        print("✅ 定时/循环任务调度线程已启动")
    except Exception as e:
        print(f"⚠️ 启动定时调度线程失败: {e}")


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "航班信息API服务正在运行", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务正常运行"}

# 注意：任务相关的路由已迁移到 api.endpoints.task_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这些路由可以作为备用
# 但正常情况下应该使用 router 中的路由

# 注意：航班相关的路由已迁移到 api.endpoints.flight_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这些路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.get("/api/flights")
# async def get_flights(...)
# @app.get("/api/flights/statistics")
# async def get_flight_statistics(...)
# @app.post("/api/flights/batch-save")
# async def batch_save_flights(...)

# 注册路由（仅在本地环境）
try:
    from api.endpoints.flight_endpoints import router as flight_router
    HAS_FLIGHT_ROUTER = True
except ImportError as e:
    print(f"⚠️ 航班路由导入失败: {e}")
    HAS_FLIGHT_ROUTER = False
    flight_router = None

if HAS_ROUTERS:
    print("✅ 注册路由...")
    app.include_router(task_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    if HAS_FLIGHT_ROUTER and flight_router:
        app.include_router(flight_router, prefix="/api")
    print("✅ 路由注册完成")
else:
    print("❌ 路由未注册，HAS_ROUTERS=False")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
