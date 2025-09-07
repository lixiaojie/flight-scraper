"""
Task management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.task import Task, TaskStatus, TaskType, TaskValidity
from app.models.flight_data import FlightData
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new scraping task"""
    
    try:
        task_service = TaskService(db)
        task = await task_service.create_task(task_data)
        return task
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating task: {str(e)}")


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    db: Session = Depends(get_db)
):
    """Get list of tasks with filtering and pagination"""
    
    try:
        task_service = TaskService(db)
        tasks, total = await task_service.get_tasks(
            skip=skip,
            limit=limit,
            status=status,
            task_type=task_type
        )
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    
    try:
        task_service = TaskService(db)
        task = await task_service.get_task_by_id(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    
    try:
        task_service = TaskService(db)
        task = await task_service.update_task(task_id, task_data)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating task: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Delete a task"""
    
    try:
        task_service = TaskService(db)
        success = await task_service.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")


@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Start a task execution"""
    
    try:
        task_service = TaskService(db)
        success = await task_service.start_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be started")
            
        return {"message": "Task started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error starting task: {str(e)}")


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Stop a running task"""
    
    try:
        task_service = TaskService(db)
        success = await task_service.stop_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be stopped")
            
        return {"message": "Task stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error stopping task: {str(e)}")


@router.get("/{task_id}/results")
async def get_task_results(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get flight data results for a task"""
    
    try:
        task_service = TaskService(db)
        results = await task_service.get_task_results(task_id)
        
        if results is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return {"results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task results: {str(e)}")


@router.get("/{task_id}/export")
async def export_task_results(
    task_id: int,
    format: str = Query("csv", regex="^(csv|excel)$"),
    db: Session = Depends(get_db)
):
    """Export task results in specified format"""
    
    try:
        task_service = TaskService(db)
        export_data = await task_service.export_task_results(task_id, format)
        
        if export_data is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting task results: {str(e)}")
