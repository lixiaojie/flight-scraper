"""
任务管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.core.database import get_db
from backend.services.task_service import TaskService
from backend.models.task_record import TaskRecord
from backend.schemas.task_schema import TaskRecordResponse, TaskStatisticsResponse, CreateTaskRequest

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskRecordResponse])
async def get_task_records(
    limit: int = Query(50, description="返回数量限制"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    db: Session = Depends(get_db)
):
    """获取任务记录列表"""
    try:
        task_service = TaskService(db)
        task_records = task_service.get_task_records(limit=limit, status=status)
        
        return [task.to_dict() for task in task_records]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}", response_model=TaskRecordResponse)
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
    """创建任务记录"""
    try:
        task_service = TaskService(db)
        task_record = task_service.create_task_record(
            task_name=request.task_name,
            task_type=request.task_type,
            source=request.source,
            config=request.config
        )
        
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

@router.get("/statistics", response_model=TaskStatisticsResponse)
async def get_task_statistics(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        task_service = TaskService(db)
        statistics = task_service.get_task_statistics()
        
        return statistics
        
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
