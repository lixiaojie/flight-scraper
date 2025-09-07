"""
Task service for managing scraping tasks
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from typing import List, Optional, Tuple
from datetime import datetime
from loguru import logger

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.core.celery import celery_app


class TaskService:
    """Service for managing tasks"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """Create a new task"""
        task = Task(**task_data.dict())
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # Schedule task if it's instant
        if task.task_validity == "instant":
            await self._schedule_task(task.id)
        
        return TaskResponse.from_orm(task)
    
    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None
    ) -> Tuple[List[TaskResponse], int]:
        """Get tasks with filtering and pagination"""
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        if task_type:
            query = query.filter(Task.task_type == task_type)
        
        total = query.count()
        tasks = query.order_by(desc(Task.created_at)).offset(skip).limit(limit).all()
        
        return [TaskResponse.from_orm(task) for task in tasks], total
    
    async def get_task_by_id(self, task_id: int) -> Optional[TaskResponse]:
        """Get a task by ID"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        return TaskResponse.from_orm(task) if task else None
    
    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[TaskResponse]:
        """Update a task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        
        return TaskResponse.from_orm(task)
    
    async def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    async def start_task(self, task_id: int) -> bool:
        """Start a task execution"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self.db.commit()
        
        # Start the scraping task
        await self._schedule_task(task_id)
        return True
    
    async def stop_task(self, task_id: int) -> bool:
        """Stop a running task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != TaskStatus.RUNNING:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        # Cancel the Celery task
        # This would require storing Celery task IDs
        return True
    
    async def get_task_results(self, task_id: int) -> Optional[List[dict]]:
        """Get flight data results for a task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # This would return flight data from the database
        # Implementation depends on the FlightData model
        return []
    
    async def export_task_results(self, task_id: int, format: str) -> Optional[dict]:
        """Export task results in specified format"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # This would generate export data
        # Implementation depends on requirements
        return {"message": f"Export in {format} format not yet implemented"}
    
    async def _schedule_task(self, task_id: int):
        """Schedule a task for execution"""
        from app.tasks.scraping_tasks import scrape_flight_task
        from app.models.platform import Platform
        
        # Get active platforms
        platforms = self.db.query(Platform).filter(Platform.is_active == True).all()
        platform_ids = [p.id for p in platforms]
        
        if platform_ids:
            # Schedule the Celery task
            scrape_flight_task.delay(task_id, platform_ids)
            logger.info(f"Scheduled task {task_id} with {len(platform_ids)} platforms")
        else:
            logger.warning(f"No active platforms found for task {task_id}")
