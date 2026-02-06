"""
任务管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import pytz

from core.database import get_db
from services.task_service import TaskService
from models.task_record import TaskRecord
from schemas.task_schema import (
    TaskRecordResponse, TaskStatisticsResponse, CreateTaskRequest,
    BatchCreateTaskRequest, TaskSummaryResponse, BatchTaskSummaryResponse,
    UpdateTaskNotesRequest
)
try:
    from services.task_scheduler import TaskScheduler
    from services.task_summary import TaskSummaryService
    HAS_SCHEDULER = True
except ImportError as e:
    print(f"⚠️ 任务调度器和摘要服务导入失败: {e}")
    HAS_SCHEDULER = False
    TaskScheduler = None
    TaskSummaryService = None

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ============================================================================
# 路由顺序说明（FastAPI路由匹配规则）：
# 1. 具体路径必须在参数路径之前
# 2. 更长的路径必须在更短的路径之前
# 3. 相同路径但不同HTTP方法的路由可以共存
# ============================================================================

# ============================================================================
# 具体路径路由（按路径长度和具体程度排序）
# ============================================================================

# 1. 最具体的路径：/summary/range
@router.get("/summary/range", response_model=List[TaskSummaryResponse])
async def get_task_summary_by_range(
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    db: Session = Depends(get_db)
):
    """根据日期范围获取任务摘要"""
    if not HAS_SCHEDULER or TaskSummaryService is None:
        raise HTTPException(status_code=503, detail="任务摘要服务不可用")
    try:
        from datetime import datetime
        
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except Exception:
                raise HTTPException(status_code=400, detail="开始日期格式错误")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except Exception:
                raise HTTPException(status_code=400, detail="结束日期格式错误")
        
        summary_service = TaskSummaryService(db)
        summaries = summary_service.generate_summary_by_date_range(
            start_date=start_dt,
            end_date=end_dt,
            status=status
        )
        
        return summaries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 具体路径：/batch/summary
@router.post("/batch/summary", response_model=BatchTaskSummaryResponse)
async def get_batch_task_summary(
    task_ids: List[int] = Body(..., description="任务ID列表"),
    db: Session = Depends(get_db)
):
    """批量获取任务摘要"""
    if not HAS_SCHEDULER or TaskSummaryService is None:
        raise HTTPException(status_code=503, detail="任务摘要服务不可用")
    try:
        summary_service = TaskSummaryService(db)
        summaries = summary_service.generate_batch_summary(task_ids)
        statistics = summary_service.generate_summary_statistics(task_ids)
        
        return {
            "summaries": summaries,
            "statistics": statistics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. 具体路径：/batch
@router.post("/batch", response_model=List[TaskRecordResponse])
async def create_batch_tasks(
    request: BatchCreateTaskRequest,
    db: Session = Depends(get_db)
):
    """批量创建任务并按计划执行"""
    if not HAS_SCHEDULER or TaskScheduler is None:
        raise HTTPException(status_code=503, detail="任务调度器服务不可用")
    try:
        scheduler = TaskScheduler(db)
        created_tasks = scheduler.create_batch_tasks(
            tasks=request.tasks,
            execute_immediately=request.execute_immediately,
            sequential=request.sequential
        )
        
        return [task.to_dict() for task in created_tasks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. 具体路径：/stats
@router.get("/stats", response_model=TaskStatisticsResponse)
async def get_task_statistics(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        task_service = TaskService(db)
        statistics = task_service.get_task_statistics()

        return statistics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. 具体路径：/cleanup
@router.delete("/cleanup")
async def cleanup_old_tasks(
    days: int = Query(30, description="保留天数"),
    db: Session = Depends(get_db)
):
    """清理旧任务记录"""
    try:
        task_service = TaskService(db)
        deleted_count = task_service.delete_old_tasks(days)

        return {"message": f"成功删除 {deleted_count} 条旧任务记录"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# 根路径路由（必须在参数路径之前）
# ============================================================================

# 5b. 具体路径：/cancel-all
@router.put("/cancel-all")
async def cancel_all_tasks(db: Session = Depends(get_db)):
    """全部取消：将当前所有运行中、排队中的任务设为已取消并终止对应子进程。"""
    try:
        targets = (
            db.query(TaskRecord)
            .filter(TaskRecord.status.in_(["running", "waiting"]))
            .all()
        )
        cancelled_ids = []
        for task in targets:
            try:
                from task_process_registry import cancel_task as kill_process
                kill_process(task.id)
            except ImportError:
                pass
            task.status = "cancelled"
            task.current_step = "已取消"
            if not task.end_time:
                task.end_time = datetime.now(pytz.timezone("Asia/Shanghai")).replace(tzinfo=None)
            cancelled_ids.append(task.id)
        if cancelled_ids:
            db.commit()
        return {"message": "已全部取消", "cancelled_count": len(cancelled_ids), "cancelled_ids": cancelled_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. 根路径：GET /
@router.get("/", response_model=List[TaskRecordResponse])
async def get_task_records(
    limit: int = Query(50, description="返回数量限制"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    db: Session = Depends(get_db)
):
    """获取任务记录列表"""
    try:
        task_service = TaskService(db)
        task_records = task_service.get_task_records(
            limit=limit, status=status)

        return [task.to_dict() for task in task_records]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. 根路径：POST /
@router.post("/", response_model=TaskRecordResponse)
async def create_task_record(
    request: CreateTaskRequest,
    db: Session = Depends(get_db)
):
    """创建任务记录并启动后台抓取脚本"""
    import threading
    import json

    try:
        task_service = TaskService(db)
        task_name = request.task_name if request.task_name and request.task_name.strip() else None
        run_mode = (request.run_mode or "immediate").strip() or "immediate"
        schedule_time_dt = None
        recurrence_end_at_dt = None
        shanghai_tz = pytz.timezone("Asia/Shanghai")

        def _parse_iso(s: str):
            if not s:
                return None
            try:
                s = s.replace("Z", "+00:00").strip()
                dt = datetime.fromisoformat(s)
                if dt.tzinfo:
                    return dt.astimezone(shanghai_tz).replace(tzinfo=None)
                return shanghai_tz.localize(dt).replace(tzinfo=None)
            except Exception:
                return None

        if request.schedule_time:
            schedule_time_dt = _parse_iso(request.schedule_time)
        if request.recurrence_end_at:
            recurrence_end_at_dt = _parse_iso(request.recurrence_end_at)
        task_record = task_service.create_task_record(
            task_name=task_name or "",
            task_type=request.task_type,
            source=request.source,
            config=request.config,
            airline=request.airline,
            run_mode=run_mode,
            schedule_time=schedule_time_dt,
            recurrence_interval_hours=request.recurrence_interval_hours,
            recurrence_end_type=request.recurrence_end_type,
            recurrence_max_runs=request.recurrence_max_runs,
            recurrence_end_at=recurrence_end_at_dt,
            recurrence_run_index=1,
        )

        # 如果任务是 flight_scraper 且为立即执行，才启动后台线程；定时/循环由调度器触发
        # 以请求中的 run_mode 为准；若未传则默认 immediate，确保「立即执行」会启动
        is_immediate = (run_mode or "immediate").strip() in ("", "immediate")
        if request.task_type == 'flight_scraper' and request.source == '12306' and is_immediate:
            import logging
            logger = logging.getLogger(__name__)
            try:
                if HAS_SCHEDULER and TaskScheduler is not None:
                    scheduler = TaskScheduler(db)
                    running_after = db.query(TaskRecord).filter(
                        TaskRecord.status == 'running',
                        TaskRecord.id != task_record.id
                    ).count() > 0
                    if running_after:
                        task_record.status = 'waiting'
                        task_record.current_step = '排队等待中'
                        db.commit()
                        logger.info(f"✅ 任务 {task_record.id} 已创建，状态为排队中（前序任务执行中）")
                    else:
                        task_record.status = 'running'
                        task_record.current_step = '等待执行'
                        db.commit()
                        logger.info(f"✅ 任务 {task_record.id} 已创建，状态设置为running，准备启动执行线程")

                    if not running_after:
                        t = threading.Thread(
                            target=scheduler.run_task_and_continue,
                            args=(task_record.id,),
                            daemon=True,
                            name=f"Task-{task_record.id}"
                        )
                        t.start()
                        logger.info(f"✅ 任务 {task_record.id} 执行线程已启动 (线程名: {t.name})")
                        import time
                        time.sleep(0.1)
                        if not t.is_alive():
                            logger.warning(f"⚠️ 任务 {task_record.id} 执行线程可能已立即退出")
                else:
                    # 回退到直接调用（如果调度器不可用）
                    logger.warning(f"⚠️ TaskScheduler 不可用，任务 {task_record.id} 无法执行，使用回退方案")
                    import sys
                    import os
                    backend_dir = os.path.dirname(
                        os.path.dirname(os.path.dirname(__file__)))
                    docker_main_path = os.path.join(backend_dir, 'docker_main.py')

                    if os.path.exists(docker_main_path):
                        # 动态导入_run_scraper_and_update函数
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            "docker_main", docker_main_path)
                        docker_main = importlib.util.module_from_spec(spec)
                        # 设置sys.path以确保模块可以导入依赖
                        sys.path.insert(0, backend_dir)
                        spec.loader.exec_module(docker_main)
                        _run_scraper_and_update = getattr(
                            docker_main, '_run_scraper_and_update', None)

                        if _run_scraper_and_update:
                            # 将config转换为JSON字符串
                            cfg_json = None
                            if request.config:
                                try:
                                    cfg_json = json.dumps(
                                        request.config, ensure_ascii=False)
                                except Exception:
                                    cfg_json = None

                            # 启动后台线程运行抓取脚本
                            def run_task():
                                _run_scraper_and_update(task_record.id, cfg_json)
                            
                            t = threading.Thread(
                                target=run_task,
                                daemon=True
                            )
                            t.start()
                            logger.info(f"已启动后台抓取脚本，任务ID: {task_record.id}")
                        else:
                            logger.warning("未找到_run_scraper_and_update函数")
            except Exception as e:
                # 如果导入失败，记录错误但不阻止任务创建
                logger.error(f"启动抓取脚本失败: {e}", exc_info=True)

        return task_record.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# 参数路径路由（必须在所有具体路径之后，按路径长度排序）
# ============================================================================

# 8. 参数路径：/{task_id:int}/summary（必须在 /{task_id:int} 之前）
@router.get("/{task_id:int}/summary", response_model=TaskSummaryResponse)
async def get_task_summary(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务摘要"""
    if not HAS_SCHEDULER or TaskSummaryService is None:
        raise HTTPException(status_code=503, detail="任务摘要服务不可用")
    try:
        summary_service = TaskSummaryService(db)
        summary = summary_service.generate_task_summary(task_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="任务记录未找到")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 9. 参数路径：/{task_id}/result
@router.put("/{task_id}/result")
async def update_task_result(
    task_id: int,
    success: bool,
    flights_count: int = 0,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新任务结果"""
    try:
        task_service = TaskService(db)
        result = task_service.update_task_result(
            task_id=task_id,
            success=success,
            flights_count=flights_count,
            error_message=error_message
        )

        if not result:
            raise HTTPException(status_code=404, detail="任务记录未找到")

        return {"message": "任务结果更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 10. 参数路径：/{task_id}/notes
@router.put("/{task_id}/notes")
async def update_task_notes(
    task_id: int,
    request: UpdateTaskNotesRequest,
    db: Session = Depends(get_db)
):
    """更新任务记录的notes字段"""
    try:
        task_service = TaskService(db)
        result = task_service.update_task_notes(
            task_id=task_id,
            notes=request.notes
        )

        if not result:
            raise HTTPException(status_code=404, detail="任务记录未找到")

        return {"message": "任务notes更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 10b. 参数路径：/{task_id:int}/cancel
@router.put("/{task_id:int}/cancel")
async def cancel_task_record(
    task_id: int,
    db: Session = Depends(get_db)
):
    """取消任务：若正在运行则终止子进程，并将状态设为已取消。仅对 running/waiting 有效。"""
    try:
        task_record = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if not task_record:
            raise HTTPException(status_code=404, detail="任务记录未找到")
        if task_record.status not in ("running", "waiting"):
            raise HTTPException(
                status_code=400,
                detail=f"仅可取消运行中或排队中的任务，当前状态: {task_record.status}",
            )
        try:
            from task_process_registry import cancel_task as kill_process
            kill_process(task_id)
        except ImportError:
            pass
        task_record.status = "cancelled"
        task_record.current_step = "已取消"
        if not task_record.end_time:
            task_record.end_time = datetime.now(pytz.timezone("Asia/Shanghai")).replace(tzinfo=None)
        db.commit()
        return {"message": "任务已取消"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 11. 参数路径：/{task_id:int}（必须在所有更具体的参数路径之后）
@router.get("/{task_id:int}", response_model=TaskRecordResponse)
async def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    """根据ID获取任务记录"""
    try:
        task_service = TaskService(db)
        task_record = task_service.get_task_by_id(task_id)

        if not task_record:
            raise HTTPException(status_code=404, detail="任务记录未找到")

        return task_record.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
