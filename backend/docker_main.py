"""
Docker容器专用的FastAPI主应用
"""

from fastapi import FastAPI, Depends, HTTPException, Request
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

from core.database import get_db
from models.flight_result import FlightResult
from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
from models.task_record import TaskRecord

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

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _ensure_task_config_column(db: Session) -> None:
    """确保 task_records 表存在 config 列（SQLite 运行时自修复）。"""
    try:
        cols = db.execute("PRAGMA table_info('task_records')").fetchall()
        col_names = {c[1] for c in cols}
        if 'config' not in col_names:
            db.execute("ALTER TABLE task_records ADD COLUMN config TEXT")
            db.commit()
    except Exception:
        db.rollback()
        # 忽略，后续会回退到写入 notes
        pass

@app.get("/")
async def root():
    """根路径"""
    return {"message": "航班信息API服务正在运行", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "flight-scraper-api"}

@app.get("/api/flights", response_model=List[FlightResultResponse])
async def get_flights(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    airline: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取航班列表"""
    try:
        query = db.query(FlightResult)
        
        if min_price is not None:
            query = query.filter(FlightResult.price >= min_price)
        if max_price is not None:
            query = query.filter(FlightResult.price <= max_price)
        if airline:
            query = query.filter(FlightResult.airline.contains(airline))
        
        flights = query.order_by(FlightResult.scrape_time.desc()).limit(limit).all()
        return [flight.to_dict() for flight in flights]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flights/statistics", response_model=FlightStatisticsResponse)
async def get_flight_statistics(db: Session = Depends(get_db)):
    """获取航班统计信息"""
    try:
        total_flights = db.query(FlightResult).count()
        min_price = db.query(FlightResult).with_entities(FlightResult.price).order_by(FlightResult.price).first()
        max_price = db.query(FlightResult).with_entities(FlightResult.price).order_by(FlightResult.price.desc()).first()
        
        if total_flights > 0:
            avg_price = db.query(FlightResult).with_entities(FlightResult.price).all()
            avg_price = sum([f.price for f in avg_price]) / len(avg_price)
        else:
            avg_price = 0.0
        
        return {
            "total_flights": total_flights,
            "min_price": min_price[0] if min_price else 0.0,
            "max_price": max_price[0] if max_price else 0.0,
            "avg_price": avg_price
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flights/batch-save")
async def batch_save_flights(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量保存航班数据"""
    try:
        flights = request.get('flights', [])
        source = request.get('source', '12306')
        saved_count = 0

        for flight_data in flights:
            flight_result = FlightResult(
                airline=flight_data.get('airline', ''),
                flight_number=flight_data.get('flight_number', ''),
                is_shared_flight=flight_data.get('is_shared_flight', ''),
                aircraft_type=flight_data.get('aircraft_type', ''),
                departure_date=flight_data.get('departure_date', ''),
                departure_time=flight_data.get('departure_time', ''),
                departure_airport=flight_data.get('departure_airport', ''),
                departure_city=flight_data.get('departure_city', ''),
                arrival_time=flight_data.get('arrival_time', ''),
                arrival_airport=flight_data.get('arrival_airport', ''),
                arrival_city=flight_data.get('arrival_city', ''),
                flight_duration=flight_data.get('flight_duration', ''),
                has_stopover=flight_data.get('has_stopover', ''),
                stopover_city=flight_data.get('stopover_city', ''),
                stopover_airport=flight_data.get('stopover_airport', ''),
                price=flight_data.get('price', 0.0),
                currency=flight_data.get('currency', 'CNY'),
                cabin_class=flight_data.get('cabin_class', ''),
                discount_rate=flight_data.get('discount_rate', ''),
                original_price=flight_data.get('original_price'),
                source=source,
                status=flight_data.get('status', 'active'),
                raw_data=str(flight_data),
                notes=flight_data.get('notes', '')
            )
            db.add(flight_result)
            saved_count += 1
        db.commit()
        
        return {"message": f"Successfully saved {saved_count} flights"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks")
async def get_task_records(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取任务记录列表"""
    try:
        query = db.query(TaskRecord)
        if status:
            query = query.filter(TaskRecord.status == status)
        records = (
            query.order_by(TaskRecord.start_time.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/statistics")
async def get_task_statistics(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        total = db.query(TaskRecord).count()
        successful = db.query(TaskRecord).filter(TaskRecord.success == True).count()  # noqa: E712
        failed = db.query(TaskRecord).filter(TaskRecord.success == False).count()  # noqa: E712
        running = db.query(TaskRecord).filter(TaskRecord.status == "running").count()

        # 平均时长（秒）
        durations = [r.duration for r in db.query(TaskRecord).filter(TaskRecord.duration.isnot(None)).all()]
        avg_duration = int(sum(durations) / len(durations)) if durations else 0

        # 总航班数（简单汇总）
        total_flights = sum([r.flights_count or 0 for r in db.query(TaskRecord).all()])

        success_rate = round((successful / total) * 100, 2) if total else 0.0

        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": failed,
            "running_tasks": running,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_flights": total_flights,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateTaskRequest(BaseModel):
    task_name: Optional[str] = None
    task_type: Optional[str] = "flight_scraper"
    source: Optional[str] = "12306"
    # 允许前端传入配置，如 { fromCity, toCity, departDate }
    config: Optional[dict] = None

def _inject_config_env(env: Dict[str, str], cfg: Optional[Dict[str, Any]]):
    """将前端配置注入为脚本可读取的环境变量"""
    if not cfg:
        return
    try:
        if cfg.get('fromCity'):
            env['SCRAPER_FROM_CITY'] = str(cfg['fromCity'])
        if cfg.get('toCity'):
            env['SCRAPER_TO_CITY'] = str(cfg['toCity'])
        if cfg.get('departDate'):
            env['SCRAPER_DEPART_DATE'] = str(cfg['departDate'])
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
            script_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "scripts", "flight_scraper_12306.py"))

        env = os.environ.copy()
        # 传递Appium地址和截图目录给脚本
        env.setdefault("APPIUM_SERVER_URL", os.environ.get("APPIUM_SERVER_URL", "http://localhost:4723"))
        env.setdefault("SCRAPER_OUTPUT_DIR", os.environ.get("SCRAPER_OUTPUT_DIR", "/app/results"))
        # 传递后端API地址给脚本
        env.setdefault("API_BASE_URL", "http://localhost:8000")
        # 传递任务ID给脚本
        env.setdefault("TASK_ID", str(task_id))
        # 允许指定宿主机已运行的 Android Studio 模拟器 udid（例如 emulator-5554）
        if os.environ.get("SCRAPER_DEVICE_UDID"):
            env["SCRAPER_DEVICE_UDID"] = os.environ["SCRAPER_DEVICE_UDID"]
        # 从参数或DB注入脚本环境变量
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
                    cfg_dict = json.loads(task.config) if isinstance(task.config, str) else task.config
                except Exception:
                    cfg_dict = None
            _inject_config_env(env, cfg_dict)
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
                    f"SCRAPER_FROM_CITY={env.get('SCRAPER_FROM_CITY','')}\n"
                    f"SCRAPER_TO_CITY={env.get('SCRAPER_TO_CITY','')}\n"
                    f"SCRAPER_DEPART_DATE={env.get('SCRAPER_DEPART_DATE','')}\n"
                ).encode('utf-8')
                lf.write(preface)
        except Exception:
            pass

        proc = subprocess.Popen(["python3", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = proc.communicate()

        try:
            with open(log_path, 'ab') as lf:
                lf.write(b"===== STDOUT =====\n")
                lf.write(stdout or b"")
                lf.write(b"\n===== STDERR =====\n")
                lf.write(stderr or b"")
        except Exception:
            pass

        task.end_time = datetime.now()
        task.duration = int(time.time() - start_ts)
        task.status = "completed"
        task.success = proc.returncode == 0
        err_text = (stderr.decode("utf-8", errors="ignore") if stderr else "").strip()
        if not task.success:
            # 将最后一段错误写入 error_message，避免过长
            task.error_message = (err_text[-900:] if err_text else "执行失败")
        else:
            task.error_message = None

        # 统计航班数量
        if task.success:
            try:
                from models.flight_result import FlightResult
                # 查询最近保存的航班数量（基于抓取时间）
                flight_count = db_session.query(FlightResult).filter(
                    FlightResult.scrape_time >= task.start_time,
                    FlightResult.source == task.source
                ).count()
                task.flights_count = flight_count
                print(f"📊 任务 {task_id} 统计到 {flight_count} 条航班数据")
            except Exception as e:
                print(f"⚠️ 统计航班数量失败: {e}")
                task.flights_count = 0
        else:
            task.flights_count = 0
        
        db_session.commit()
    except Exception as e:
        try:
            task = db_session.query(TaskRecord).get(task_id)
            if task:
                task.end_time = datetime.now()
                task.duration = int(time.time() - start_ts)
                task.status = "failed"
                task.success = False
                task.error_message = str(e)[:1000]
                db_session.commit()
        finally:
            pass
    finally:
        db_session.close()

@app.post("/api/tasks")
async def create_task(req: Request, db: Session = Depends(get_db)):
    """创建抓取任务并启动后台执行"""
    try:
        # 读取原始 JSON
        try:
            request: Dict[str, Any] = await req.json()
        except Exception:
            request = {}

        source = request.get('source') or '12306'
        task_type = request.get('task_type') or 'flight_scraper'
        config_obj = request.get('config')

        if source != "12306":
            raise HTTPException(status_code=400, detail="目前仅支持12306脚本")

        import json
        cfg_json = None
        try:
            if config_obj is not None:
                cfg_json = json.dumps(config_obj, ensure_ascii=False)
        except Exception:
            cfg_json = None

        task = TaskRecord(
            task_name=(
                (request.get('task_name') or None)
                or f"抓取任务-{source}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            task_type=task_type,
            status="running",
            source=source,
            success=False,
            flights_count=0,
            config=cfg_json,
        )
        # 确保存在 config 列并写入
        _ensure_task_config_column(db)
        try:
            db.add(task)
            db.commit()
            db.refresh(task)
        except Exception:
            db.rollback()
            # 回退：将配置写入 notes 字段
            task.config = None
            task.notes = (cfg_json or "")[:1000]
            db.add(task)
            db.commit()
            db.refresh(task)

        # 启动后台线程运行脚本，直接传入本次配置，避免依赖 DB 读取
        t = threading.Thread(target=_run_scraper_and_update, args=(task.id, cfg_json), daemon=True)
        t.start()

        data = task.to_dict()
        data['config_received'] = config_obj
        return data
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: int, request: Request, db: Session = Depends(get_db)):
    """更新任务状态"""
    try:
        # 读取请求数据
        try:
            data = await request.json()
        except Exception:
            data = {}
        
        current_step = data.get('current_step')
        status = data.get('status')
        
        # 查找任务
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 更新状态
        if current_step:
            task.current_step = current_step
        if status:
            task.status = status
        
        db.commit()
        db.refresh(task)
        
        return {"message": "状态更新成功", "task": task.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/login")
async def admin_login(request: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    try:
        if request.username == 'admin' and request.password == 'admin123':
            return {
                "access_token": "fake-jwt-token",
                "token_type": "bearer",
                "admin": {
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

@app.post("/api/v1/auth/login")
async def auth_login(request: dict, db: Session = Depends(get_db)):
    """兼容前端的登录接口 - 宽松版本"""
    try:
        # 尝试从不同的字段名获取用户名和密码
        username = request.get('username') or request.get('user') or request.get('email')
        password = request.get('password') or request.get('pass') or request.get('pwd')
        
        if (username == 'admin' or username == 'admin@flight-scraper.com') and password == 'admin123':
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
        "keys": list(request.keys()) if isinstance(request, dict) else "Not a dict"
    }

# 添加一个更宽松的登录接口
@app.post("/api/v1/auth/login-flexible")
async def auth_login_flexible(request: dict, db: Session = Depends(get_db)):
    """灵活的登录接口 - 接受任何格式的请求"""
    try:
        # 尝试从不同的字段名获取用户名和密码
        username = request.get('username') or request.get('user') or request.get('email')
        password = request.get('password') or request.get('pass') or request.get('pwd')
        
        if (username == 'admin' or username == 'admin@flight-scraper.com') and password == 'admin123':
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

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    try:
        return {
            "web": "running",
            "frontend": "running",
            "appium": "unknown",
            "android": "unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
