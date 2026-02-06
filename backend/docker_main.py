"""
Docker容器专用的FastAPI主应用
"""

from models.task_record import TaskRecord
from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
from models.flight_result import FlightResult
from core.database import get_db
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
import sys
import os
import threading
import subprocess
import time
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# 导入API路由
try:
    from api.endpoints.task_endpoints import router as task_router
    from api.endpoints.admin_endpoints import router as admin_router
    from api.endpoints.system_endpoints import router as system_router
    from api.endpoints.flight_endpoints import router as flight_router
    HAS_ROUTERS = True
    print("✅ 路由导入成功")
except ImportError as e:
    print(f"❌ 路由导入失败: {e}")
    HAS_ROUTERS = False

# 定义请求模型


class LoginRequest(BaseModel):
    username: str
    password: str


# 创建FastAPI应用
app = FastAPI(
    title="航班信息API",
    description="12306航班信息抓取和查询API",
    version="1.0.0"
)
# 挂载结果目录用于静态访问（用于调试/比对）
try:
    results_dir = os.environ.get("SCRAPER_OUTPUT_DIR", "/app/results")
    os.makedirs(results_dir, exist_ok=True)
    app.mount("/results", StaticFiles(directory=results_dir), name="results")
except Exception:
    pass

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
if HAS_ROUTERS:
    print("✅ 注册路由...")
    app.include_router(task_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    app.include_router(flight_router, prefix="/api")
    print("✅ 路由注册完成")
else:
    print("❌ 路由未注册，HAS_ROUTERS=False")


def _ensure_task_config_column(db: Session) -> None:
    """确保 task_records 表存在 config 列及定时/循环相关列（SQLite 运行时自修复）。"""
    try:
        from sqlalchemy import text
        cols = db.execute(text("PRAGMA table_info('task_records')")).fetchall()
        col_names = {c[1] for c in cols}
        if 'config' not in col_names:
            db.execute(text("ALTER TABLE task_records ADD COLUMN config TEXT"))
        for col, typ in [
            ('run_mode', 'VARCHAR(20)'),
            ('schedule_time', 'DATETIME'),
            ('recurrence_interval_hours', 'INTEGER'),
            ('recurrence_end_type', 'VARCHAR(20)'),
            ('recurrence_max_runs', 'INTEGER'),
            ('recurrence_end_at', 'DATETIME'),
            ('recurrence_run_index', 'INTEGER'),
        ]:
            if col not in col_names:
                db.execute(text(f"ALTER TABLE task_records ADD COLUMN {col} {typ}"))
        db.commit()
    except Exception:
        db.rollback()
        pass


@app.on_event("startup")
def _startup_ensure_columns():
    """启动时确保 task_records 表具备定时/循环等列，并启动定时调度线程"""
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        try:
            _ensure_task_config_column(db)
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ 启动时检查 task_records 列失败: {e}")
    try:
        import threading
        from services.schedule_runner import _run_schedule_loop
        t = threading.Thread(target=_run_schedule_loop, daemon=True, name="ScheduleRunner")
        t.start()
        print("✅ 定时/循环任务调度线程已启动")
    except Exception as e:
        print(f"⚠️ 启动定时调度线程失败: {e}")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "航班信息API服务正在运行", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "flight-scraper-api"}


# 注意：航班相关的路由已迁移到 api.endpoints.flight_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这些路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.get("/api/flights/statistics")
# async def get_flight_statistics(...)

# 注意：航班批量保存路由已迁移到 api.endpoints.flight_endpoints
# 这里保留注释以避免路由冲突
# @app.post("/api/flights/batch-save")
# async def batch_save_flights(...)

# 注意：任务相关的路由已迁移到 api.endpoints.task_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这些路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.get("/api/tasks")
# async def get_task_records(...)

# 注意：任务统计路由已迁移到 api.endpoints.task_endpoints
# 这里保留注释以避免路由冲突
# @app.get("/api/tasks/statistics")
# async def get_task_statistics(...)


class CreateTaskRequest(BaseModel):
    task_name: Optional[str] = None
    task_type: Optional[str] = "flight_scraper"
    source: Optional[str] = "12306"
    # 允许前端传入配置，如 { fromCity, toCity, departDate }
    config: Optional[dict] = None


def _inject_config_env(env: Dict[str, str], cfg: Optional[Dict[str, Any]], task_airline: Optional[str] = None):
    """将前端配置注入为脚本可读取的环境变量。航司以 task_airline 优先（来自 task.airline），其次 cfg.airline。"""
    try:
        if cfg:
            if cfg.get('fromCity'):
                env['SCRAPER_FROM_CITY'] = str(cfg['fromCity'])
            if cfg.get('toCity'):
                env['SCRAPER_TO_CITY'] = str(cfg['toCity'])
            if cfg.get('departDate'):
                env['SCRAPER_DEPART_DATE'] = str(cfg['departDate'])
            if cfg.get('airline'):
                env['SCRAPER_AIRLINE'] = str(cfg['airline'])
        if task_airline:
            env['SCRAPER_AIRLINE'] = str(task_airline)
    except Exception:
        pass


def _run_scraper_and_update(task_id: int, cfg_json: Optional[str] = None):
    """后台运行抓取脚本并更新任务状态"""
    # 延迟导入，避免与主线程会话冲突
    from core.database import SessionLocal

    db_session = SessionLocal()
    start_ts = time.time()
    try:
        task = db_session.query(TaskRecord).get(task_id)
        if not task:
            return

        # 运行抓取脚本（容器路径 /app/scripts 已挂载）
        script_path = "/app/scripts/flight_scraper_12306.py"
        if not os.path.exists(script_path):
            # 兼容在本地运行 web 主进程
            script_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(__file__)),
                    "..",
                    "scripts",
                    "flight_scraper_12306.py"))

        env = os.environ.copy()
        # 仅传递统一配置路径，其余连接参数由脚本侧读取 JSON 配置
        env.setdefault(
            "SCRAPER_CONFIG_PATH",
            os.environ.get(
                "SCRAPER_CONFIG_PATH",
                "/app/scripts/config/scraper.config.json"))
        # 可选：输出目录、后端地址、任务ID
        env.setdefault(
            "SCRAPER_OUTPUT_DIR",
            os.environ.get(
                "SCRAPER_OUTPUT_DIR",
                "/app/results"))
        env.setdefault("API_BASE_URL", "http://localhost:8000")
        env.setdefault("TASK_ID", str(task_id))
        # 从参数或DB注入业务查询配置（城市/日期等）
        try:
            import json
            cfg_dict: Optional[Dict[str, Any]] = None
            if cfg_json:
                try:
                    cfg_dict = json.loads(cfg_json)
                except Exception:
                    cfg_dict = None
            if cfg_dict is None and task.config:
                try:
                    cfg_dict = json.loads(
                        task.config) if isinstance(
                        task.config,
                        str) else task.config
                except Exception:
                    cfg_dict = None
            _inject_config_env(env, cfg_dict, task_airline=getattr(task, 'airline', None))
        except Exception:
            pass

        # 结果日志路径
        results_dir = env.get("SCRAPER_OUTPUT_DIR", "/app/results")
        os.makedirs(results_dir, exist_ok=True)
        log_path = os.path.join(results_dir, f"task-{task.id}.log")

        # 预写环境关键信息
        try:
            with open(log_path, 'wb') as lf:
                preface = (
                    f"SCRAPER_FROM_CITY={env.get('SCRAPER_FROM_CITY', '')}\n"
                    f"SCRAPER_TO_CITY={env.get('SCRAPER_TO_CITY', '')}\n"
                    f"SCRAPER_DEPART_DATE={env.get('SCRAPER_DEPART_DATE', '')}\n"
                    f"SCRAPER_AIRLINE={env.get('SCRAPER_AIRLINE', '')}\n"
                    f"SCRAPER_CONFIG_PATH={env.get('SCRAPER_CONFIG_PATH', '')}\n"
                ).encode('utf-8')
                lf.write(preface)
        except Exception:
            pass

        proc = subprocess.Popen(["python3",
                                 script_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        try:
            from task_process_registry import register, unregister
            register(task_id, proc)
        except ImportError:
            pass
        try:
            stdout, stderr = proc.communicate()
        finally:
            try:
                from task_process_registry import unregister
                unregister(task_id)
            except ImportError:
                pass

        try:
            with open(log_path, 'ab') as lf:
                lf.write(b"===== STDOUT =====\n")
                lf.write(stdout or b"")
                lf.write(b"\n===== STDERR =====\n")
                lf.write(stderr or b"")
        except Exception:
            pass

        import pytz
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        task = db_session.query(TaskRecord).get(task_id)
        if not task:
            return
        if getattr(task, 'status', None) == 'cancelled':
            if not task.end_time:
                task.end_time = datetime.now(shanghai_tz).replace(tzinfo=None)
                task.duration = int(time.time() - start_ts)
            db_session.commit()
            return
        task.end_time = datetime.now(shanghai_tz).replace(tzinfo=None)
        task.duration = int(time.time() - start_ts)
        task.status = "completed"
        task.success = proc.returncode == 0
        err_text = (
            stderr.decode(
                "utf-8",
                errors="ignore") if stderr else "").strip()
        if not task.success:
            task.error_message = (err_text[-900:] if err_text else "执行失败")
        else:
            task.error_message = None

        if task.success:
            try:
                # 使用task_id精确统计航班数量
                flight_count = db_session.query(FlightResult).filter(
                    FlightResult.task_id == task_id,
                    FlightResult.status == 'active'
                ).count()
                task.flights_count = flight_count
                print(f"📊 任务 {task_id} 统计到 {flight_count} 条航班数据（基于task_id）")
            except Exception as e:
                print(f"⚠️ 统计航班数量失败: {e}")
                import traceback
                traceback.print_exc()
                task.flights_count = 0
        else:
            task.flights_count = 0

        db_session.commit()
    except Exception as e:
        try:
            task = db_session.query(TaskRecord).get(task_id)
            if task:
                import pytz
                shanghai_tz = pytz.timezone('Asia/Shanghai')
                task.end_time = datetime.now(shanghai_tz).replace(tzinfo=None)
                task.duration = int(time.time() - start_ts)
                task.status = "failed"
                task.success = False
                task.error_message = str(e)[:1000]
                db_session.commit()
        finally:
            pass
    finally:
        db_session.close()


# 注意：任务创建路由已迁移到 api.endpoints.task_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这个路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.post("/api/tasks")
# async def create_task(...)


# 注意：任务状态更新路由已迁移到 api.endpoints.task_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这个路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.patch("/api/tasks/{task_id}/status")
# async def update_task_status(...)


# 注意：管理员登录路由已迁移到 api.endpoints.admin_endpoints
# 这里保留注释以避免路由冲突
# 如果 router 导入失败，这个路由可以作为备用
# 但正常情况下应该使用 router 中的路由
# @app.post("/api/admin/login")
# async def admin_login(...)


@app.post("/api/v1/auth/login")
async def auth_login(request: dict, db: Session = Depends(get_db)):
    """兼容前端的登录接口 - 宽松版本"""
    try:
        # 尝试从不同的字段名获取用户名和密码
        username = request.get('username') or request.get(
            'user') or request.get('email')
        password = request.get('password') or request.get(
            'pass') or request.get('pwd')

        if (username == 'admin' or username ==
                'admin@flight-scraper.com') and password == 'admin123':
            return {
                "access_token": "fake-jwt-token",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@flight-scraper.com",
                    "is_active": True,
                    "is_superuser": True
                }
            }
        else:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 添加一个调试接口来查看前端发送的数据


@app.post("/api/v1/auth/login-debug")
async def auth_login_debug(request: dict, db: Session = Depends(get_db)):
    """调试接口 - 查看前端发送的数据"""
    return {
        "received_data": request,
        "data_type": type(request).__name__,
        "keys": list(
            request.keys()) if isinstance(
            request,
            dict) else "Not a dict"}

# 添加一个更宽松的登录接口


@app.post("/api/v1/auth/login-flexible")
async def auth_login_flexible(request: dict, db: Session = Depends(get_db)):
    """灵活的登录接口 - 接受任何格式的请求"""
    try:
        # 尝试从不同的字段名获取用户名和密码
        username = request.get('username') or request.get(
            'user') or request.get('email')
        password = request.get('password') or request.get(
            'pass') or request.get('pwd')

        if (username == 'admin' or username ==
                'admin@flight-scraper.com') and password == 'admin123':
            return {
                "access_token": "fake-jwt-token",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@flight-scraper.com",
                    "is_active": True,
                    "is_superuser": True
                }
            }
        else:
            return {
                "error": "用户名或密码错误",
                "received_username": username,
                "received_password": password,
                "received_data": request
            }

    except Exception as e:
        return {
            "error": str(e),
            "received_data": request
        }


# 注意：系统状态路由已迁移到 api.endpoints.system_endpoints
# 这里保留注释以避免路由冲突
# @app.get("/api/system/status")
# async def get_system_status(...)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
