"""
任务管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from core.database import get_db
from services.task_service import TaskService
from models.task_record import TaskRecord
from schemas.task_schema import TaskRecordResponse, TaskStatisticsResponse, CreateTaskRequest

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/stats", response_model=TaskStatisticsResponse)
async def get_task_statistics(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        task_service = TaskService(db)
        statistics = task_service.get_task_statistics()

        return statistics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        # 如果task_name为空或None，传递None让service自动生成
        task_name = request.task_name if request.task_name and request.task_name.strip() else None
        task_record = task_service.create_task_record(
            task_name=task_name or "",  # 传递空字符串，service会处理None/空字符串的情况
            task_type=request.task_type,
            source=request.source,
            config=request.config,
            airline=request.airline
        )

        # 如果任务是flight_scraper类型，启动后台抓取脚本
        if request.task_type == 'flight_scraper' and request.source == '12306':
            try:
                # 尝试从docker_main模块导入_run_scraper_and_update函数
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
                        t = threading.Thread(
                            target=_run_scraper_and_update,
                            args=(task_record.id, cfg_json),
                            daemon=True
                        )
                        t.start()
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"已启动后台抓取脚本，任务ID: {task_record.id}")
                    else:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning("未找到_run_scraper_and_update函数")
            except Exception as e:
                # 如果导入失败，记录错误但不阻止任务创建
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"启动抓取脚本失败: {e}", exc_info=True)

        return task_record.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


class UpdateTaskNotesRequest(BaseModel):
    notes: str


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
