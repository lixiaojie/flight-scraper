"""
任务管理服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pytz
from models.task_record import TaskRecord
import logging
import json

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def _generate_task_name(
            self,
            task_name: Optional[str],
            config: Optional[Dict],
            source: str,
            airline: Optional[str]) -> str:
        """生成标准化的任务名称：出发城市-到达城市-出发日期-查询平台-指定航空公司"""
        # 如果提供了任务名称且不为空，直接使用
        if task_name and task_name.strip():
            return task_name.strip()

        # 否则根据配置生成标准化的任务名称
        if not config:
            return f"抓取任务-{source}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        from_city = config.get('fromCity', '未知')
        to_city = config.get('toCity', '未知')
        depart_date = config.get('departDate', '未知')
        airline_name = airline or '全部'

        return f"{from_city}-{to_city}-{depart_date}-{source}-{airline_name}"

    def create_task_record(
            self,
            task_name: Optional[str] = None,
            task_type: str = 'flight_scraper',
            source: str = '12306',
            config: Optional[Dict] = None,
            airline: Optional[str] = '深圳航空') -> TaskRecord:
        """创建任务记录"""
        try:
            # 应用新的任务命名规范：出发城市-到达城市-出发日期-查询平台-指定航空公司
            final_task_name = self._generate_task_name(
                task_name or "", config or {}, source, airline or "")

            # 将config转换为JSON字符串存储
            config_str = None
            if config:
                try:
                    config_str = json.dumps(config, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"Config序列化失败: {e}")
                    config_str = str(config)

            task_record = TaskRecord(
                task_name=final_task_name,
                task_type=task_type,
                source=source,
                config=config_str,
                airline=airline,
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

    def update_task_result(
            self,
            task_id: int,
            success: bool,
            flights_count: int = 0,
            error_message: str = None) -> bool:
        """更新任务结果"""
        try:
            task_record = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id).first()

            if not task_record:
                logger.error(f"任务记录未找到: {task_id}")
                return False

            task_record.status = 'completed'
            shanghai_tz = pytz.timezone('Asia/Shanghai')
            # 存储时区感知的时间，但在返回给前端时会转换为Asia/Shanghai时区
            task_record.end_time = datetime.now(
                shanghai_tz).replace(tzinfo=None)
            # 计算时长时确保两个时间都在同一时区
            if task_record.start_time:
                # 假设start_time已经是Asia/Shanghai时区（但存储时移除了tzinfo）
                # 计算时长时，假设它们都是naive datetime，但表示的是Asia/Shanghai时间
                start_naive = task_record.start_time if task_record.start_time.tzinfo is None else task_record.start_time.replace(
                    tzinfo=None)
                end_naive = task_record.end_time if task_record.end_time is None or task_record.end_time.tzinfo is None else task_record.end_time.replace(
                    tzinfo=None)
                task_record.duration = int(
                    (end_naive - start_naive).total_seconds()) if end_naive and start_naive else 0
            task_record.success = success
            task_record.flights_count = flights_count
            task_record.error_message = error_message

            self.db.commit()

            logger.info(
                f"任务结果已更新: {task_id}, 成功: {success}, 航班数: {flights_count}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务结果失败: {e}")
            return False

    def update_task_notes(self, task_id: int, notes: str) -> bool:
        """更新任务记录的notes字段"""
        try:
            task_record = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id).first()

            if not task_record:
                logger.error(f"任务记录未找到: {task_id}")
                return False

            # 如果已有notes，追加新内容；否则直接设置
            if task_record.notes:
                task_record.notes = f"{task_record.notes}\n{notes}"
            else:
                task_record.notes = notes

            self.db.commit()

            logger.info(f"任务notes已更新: {task_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务notes失败: {e}")
            return False

    def get_task_records(
            self,
            limit: int = 50,
            status: str = None) -> List[TaskRecord]:
        """获取任务记录列表，实时统计航班数量"""
        try:
            from models.flight_result import FlightResult

            query = self.db.query(TaskRecord)

            if status:
                query = query.filter(TaskRecord.status == status)

            task_records = query.order_by(
                desc(TaskRecord.start_time)).limit(limit).all()

            # 实时统计每个任务的航班数量
            for task_record in task_records:
                flight_count = self.db.query(FlightResult).filter(
                    FlightResult.task_id == task_record.id,
                    FlightResult.status == 'active'
                ).count()
                # 更新flights_count字段（仅在内存中，不写回数据库）
                task_record.flights_count = flight_count
                logger.debug(f"任务 {task_record.id} 实时统计航班数量: {flight_count}")

            return task_records

        except Exception as e:
            logger.error(f"获取任务记录失败: {e}")
            raise e

    def get_task_by_id(self, task_id: int) -> Optional[TaskRecord]:
        """根据ID获取任务记录，实时统计航班数量"""
        try:
            from models.flight_result import FlightResult

            task_record = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id).first()

            if task_record:
                # 实时统计该任务的航班数量
                flight_count = self.db.query(FlightResult).filter(
                    FlightResult.task_id == task_id,
                    FlightResult.status == 'active'
                ).count()
                # 更新flights_count字段（仅在内存中，不写回数据库）
                task_record.flights_count = flight_count
                logger.debug(f"任务 {task_id} 实时统计航班数量: {flight_count}")

            return task_record

        except Exception as e:
            logger.error(f"获取任务记录失败: {e}")
            return None

    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            total_tasks = self.db.query(TaskRecord).count()
            successful_tasks = self.db.query(
                TaskRecord).filter(TaskRecord.success).count()
            failed_tasks = self.db.query(TaskRecord).filter(
                TaskRecord.success == False).count()
            running_tasks = self.db.query(TaskRecord).filter(
                TaskRecord.status == 'running').count()

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
            total_flights_count = sum(
                task.flights_count for task in total_flights)

            return {
                'total_tasks': total_tasks,
                'successful_tasks': successful_tasks,
                'failed_tasks': failed_tasks,
                'running_tasks': running_tasks,
                'success_rate': round(
                    successful_tasks / total_tasks * 100,
                    2) if total_tasks > 0 else 0,
                'avg_duration': round(
                    avg_duration,
                    2),
                'total_flights': total_flights_count}

        except Exception as e:
            logger.error(f"获取任务统计信息失败: {e}")
            raise e

    def delete_old_tasks(self, days: int = 30) -> int:
        """删除旧任务记录"""
        try:
            shanghai_tz = pytz.timezone('Asia/Shanghai')
            cutoff_date = datetime.now(shanghai_tz) - timedelta(days=days)

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
