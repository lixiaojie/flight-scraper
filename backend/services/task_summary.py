"""
任务摘要生成服务
生成任务执行摘要，包含任务名称、创建时间、启动时间、结束时间、抓取结果数等
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import pytz

from models.task_record import TaskRecord
from models.flight_result import FlightResult

class TaskSummaryService:
    """任务摘要生成服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_task_summary(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        生成单个任务的摘要
        
        Returns:
            任务摘要字典，包含：
            - task_id: 任务ID
            - task_name: 任务名称
            - created_at: 创建时间
            - start_time: 启动时间
            - end_time: 结束时间
            - duration: 执行时长（秒）
            - status: 任务状态
            - success: 是否成功
            - flights_count: 抓取结果数
            - error_message: 错误信息（如果有）
        """
        try:
            task = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id).first()
            
            if not task:
                return None
            
            # 实时统计航班数量
            flights_count = self.db.query(FlightResult).filter(
                and_(
                    FlightResult.task_id == task_id,
                    FlightResult.status == 'active'
                )
            ).count()
            
            # 格式化时间
            def format_time(dt):
                if not dt:
                    return None
                if isinstance(dt, str):
                    return dt
                if isinstance(dt, datetime):
                    if dt.tzinfo is None:
                        shanghai_tz = pytz.timezone('Asia/Shanghai')
                        dt = shanghai_tz.localize(dt)
                    else:
                        shanghai_tz = pytz.timezone('Asia/Shanghai')
                        dt = dt.astimezone(shanghai_tz)
                    return dt.isoformat()
                return None
            
            return {
                'task_id': task.id,
                'task_name': task.task_name,
                'created_at': format_time(task.created_at),
                'start_time': format_time(task.start_time),
                'end_time': format_time(task.end_time),
                'duration': task.duration,
                'duration_formatted': self._format_duration(task.duration) if task.duration else None,
                'status': task.status,
                'success': task.success,
                'flights_count': flights_count,
                'error_message': task.error_message,
                'source': task.source,
                'airline': task.airline,
                'current_step': task.current_step
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"生成任务摘要失败: {e}", exc_info=True)
            return None

    def generate_batch_summary(self, task_ids: List[int]) -> List[Dict[str, Any]]:
        """
        批量生成任务摘要
        
        Args:
            task_ids: 任务ID列表
        
        Returns:
            任务摘要列表
        """
        summaries = []
        for task_id in task_ids:
            summary = self.generate_task_summary(task_id)
            if summary:
                summaries.append(summary)
        return summaries

    def generate_summary_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        根据日期范围生成任务摘要
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            status: 任务状态筛选
        
        Returns:
            任务摘要列表
        """
        try:
            query = self.db.query(TaskRecord)
            
            if start_date:
                query = query.filter(TaskRecord.created_at >= start_date)
            if end_date:
                query = query.filter(TaskRecord.created_at <= end_date)
            if status:
                query = query.filter(TaskRecord.status == status)
            
            tasks = query.order_by(TaskRecord.created_at.desc()).all()
            
            task_ids = [task.id for task in tasks]
            return self.generate_batch_summary(task_ids)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"根据日期范围生成摘要失败: {e}", exc_info=True)
            return []

    def generate_summary_statistics(
        self,
        task_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        生成摘要统计信息
        
        Args:
            task_ids: 可选的任务ID列表，如果提供则只统计这些任务
        
        Returns:
            统计信息字典
        """
        try:
            if task_ids:
                tasks = self.db.query(TaskRecord).filter(
                    TaskRecord.id.in_(task_ids)).all()
            else:
                tasks = self.db.query(TaskRecord).all()
            
            total_tasks = len(tasks)
            successful_tasks = sum(1 for t in tasks if t.success)
            failed_tasks = sum(1 for t in tasks if not t.success and t.status == 'completed')
            running_tasks = sum(1 for t in tasks if t.status == 'running')
            
            total_flights = sum(
                self.db.query(FlightResult).filter(
                    and_(
                        FlightResult.task_id == t.id,
                        FlightResult.status == 'active'
                    )
                ).count()
                for t in tasks
            )
            
            total_duration = sum(t.duration for t in tasks if t.duration)
            avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
            
            return {
                'total_tasks': total_tasks,
                'successful_tasks': successful_tasks,
                'failed_tasks': failed_tasks,
                'running_tasks': running_tasks,
                'success_rate': round(successful_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
                'total_flights': total_flights,
                'avg_duration': round(avg_duration, 2),
                'total_duration': round(total_duration, 2),
                'total_duration_formatted': self._format_duration(int(total_duration))
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"生成摘要统计失败: {e}", exc_info=True)
            return {}

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if not seconds:
            return "0秒"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if secs > 0 or not parts:
            parts.append(f"{secs}秒")
        
        return "".join(parts)
