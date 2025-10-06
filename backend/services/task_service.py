"""
任务管理服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.models.task_record import TaskRecord
import logging

logger = logging.getLogger(__name__)

class TaskService:
    """任务管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task_record(self, task_name: str, task_type: str = 'flight_scraper', 
                          source: str = '12306', config: Dict = None) -> TaskRecord:
        """创建任务记录"""
        try:
            task_record = TaskRecord(
                task_name=task_name,
                task_type=task_type,
                source=source,
                config=str(config) if config else None,
                status='running'
            )
            
            self.db.add(task_record)
            self.db.commit()
            self.db.refresh(task_record)
            
            logger.info(f"任务记录已创建: {task_name}")
            return task_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建任务记录失败: {e}")
            raise e
    
    def update_task_result(self, task_id: int, success: bool, flights_count: int = 0, 
                          error_message: str = None) -> bool:
        """更新任务结果"""
        try:
            task_record = self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
            
            if not task_record:
                logger.error(f"任务记录未找到: {task_id}")
                return False
            
            task_record.status = 'completed'
            task_record.end_time = datetime.now()
            task_record.duration = int((task_record.end_time - task_record.start_time).total_seconds())
            task_record.success = success
            task_record.flights_count = flights_count
            task_record.error_message = error_message
            
            self.db.commit()
            
            logger.info(f"任务结果已更新: {task_id}, 成功: {success}, 航班数: {flights_count}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务结果失败: {e}")
            return False
    
    def get_task_records(self, limit: int = 50, status: str = None) -> List[TaskRecord]:
        """获取任务记录列表"""
        try:
            query = self.db.query(TaskRecord)
            
            if status:
                query = query.filter(TaskRecord.status == status)
            
            task_records = query.order_by(desc(TaskRecord.start_time)).limit(limit).all()
            
            return task_records
            
        except Exception as e:
            logger.error(f"获取任务记录失败: {e}")
            raise e
    
    def get_task_by_id(self, task_id: int) -> Optional[TaskRecord]:
        """根据ID获取任务记录"""
        try:
            task_record = self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
            return task_record
            
        except Exception as e:
            logger.error(f"获取任务记录失败: {e}")
            return None
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            total_tasks = self.db.query(TaskRecord).count()
            successful_tasks = self.db.query(TaskRecord).filter(TaskRecord.success == True).count()
            failed_tasks = self.db.query(TaskRecord).filter(TaskRecord.success == False).count()
            running_tasks = self.db.query(TaskRecord).filter(TaskRecord.status == 'running').count()
            
            # 计算平均执行时间
            completed_tasks = self.db.query(TaskRecord).filter(
                TaskRecord.status == 'completed',
                TaskRecord.duration.isnot(None)
            ).all()
            
            avg_duration = 0
            if completed_tasks:
                total_duration = sum(task.duration for task in completed_tasks)
                avg_duration = total_duration / len(completed_tasks)
            
            # 计算总航班数
            total_flights = self.db.query(TaskRecord).with_entities(
                TaskRecord.flights_count
            ).all()
            total_flights_count = sum(task.flights_count for task in total_flights)
            
            return {
                'total_tasks': total_tasks,
                'successful_tasks': successful_tasks,
                'failed_tasks': failed_tasks,
                'running_tasks': running_tasks,
                'success_rate': round(successful_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
                'avg_duration': round(avg_duration, 2),
                'total_flights': total_flights_count
            }
            
        except Exception as e:
            logger.error(f"获取任务统计信息失败: {e}")
            raise e
    
    def delete_old_tasks(self, days: int = 30) -> int:
        """删除旧任务记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            old_tasks = self.db.query(TaskRecord).filter(
                TaskRecord.start_time < cutoff_date
            ).all()
            
            count = len(old_tasks)
            
            for task in old_tasks:
                self.db.delete(task)
            
            self.db.commit()
            logger.info(f"删除了 {count} 条旧任务记录")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除旧任务记录失败: {e}")
            raise e
