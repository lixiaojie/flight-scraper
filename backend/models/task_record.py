"""
抓取任务记录模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
import pytz

Base = declarative_base()


class TaskRecord(Base):
    """抓取任务记录模型"""
    __tablename__ = 'task_records'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 任务基本信息
    task_name = Column(String(100), nullable=False, comment='任务名称')
    task_type = Column(String(50), default='flight_scraper', comment='任务类型')
    status = Column(String(20), default='running', comment='任务状态')
    current_step = Column(String(100), default='初始化中', comment='当前执行步骤')

    # 执行信息
    start_time = Column(DateTime, default=lambda: datetime.now(
        pytz.timezone('Asia/Shanghai')).replace(tzinfo=None), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Integer, comment='执行时长(秒)')

    # 结果信息
    success = Column(Boolean, default=False, comment='是否成功')
    flights_count = Column(Integer, default=0, comment='抓取航班数量')
    error_message = Column(Text, comment='错误信息')

    # 配置信息
    source = Column(String(50), default='12306', comment='数据源')
    config = Column(Text, comment='任务配置')
    airline = Column(String(50), default='深圳航空', comment='指定航空公司')

    # 运行模式：immediate=立即, scheduled=定时, recurring=循环
    run_mode = Column(String(20), default='immediate', comment='运行模式')
    schedule_time = Column(DateTime, comment='计划运行时间（定时/循环首次）')
    # 循环任务
    recurrence_interval_hours = Column(Integer, comment='循环间隔（小时）')
    recurrence_end_type = Column(String(20), comment='循环终止方式: count=次数, end_time=截止时间')
    recurrence_max_runs = Column(Integer, comment='循环最大执行次数')
    recurrence_end_at = Column(DateTime, comment='循环截止时间')
    recurrence_run_index = Column(Integer, default=1, comment='当前为第几次执行（从1开始）')

    # 额外信息
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=lambda: datetime.now(
        pytz.timezone('Asia/Shanghai')).replace(tzinfo=None), comment='创建时间')

    # 索引
    __table_args__ = (
        Index('idx_task_name', 'task_name'),
        Index('idx_start_time', 'start_time'),
        Index('idx_status', 'status'),
        Index('idx_success', 'success'),
    )

    def __repr__(self):
        return f"<TaskRecord(task_name='{self.task_name}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        def format_datetime(dt):
            """格式化日期时间 - 转换为Asia/Shanghai时区"""
            if not dt:
                return None
            # 如果已经是字符串，直接返回
            if isinstance(dt, str):
                return dt
            # 如果是datetime对象，转换为Asia/Shanghai时区并格式化为ISO格式
            if isinstance(dt, datetime):
                # 如果没有时区信息，假设已经是Asia/Shanghai时区（因为创建时就是）
                if dt.tzinfo is None:
                    shanghai_tz = pytz.timezone('Asia/Shanghai')
                    # 将naive datetime视为Asia/Shanghai时区
                    dt = shanghai_tz.localize(dt)
                else:
                    # 如果有时区信息，转换为Asia/Shanghai时区
                    shanghai_tz = pytz.timezone('Asia/Shanghai')
                    dt = dt.astimezone(shanghai_tz)
            return dt.isoformat()

        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_type': self.task_type,
            'status': self.status,
            'current_step': self.current_step,
            'start_time': format_datetime(self.start_time),
            'end_time': format_datetime(self.end_time),
            'duration': self.duration,
            'success': self.success,
            'flights_count': self.flights_count,
            'error_message': self.error_message,
            'source': self.source,
            'config': self.config,
            'airline': self.airline,
            'run_mode': getattr(self, 'run_mode', None) or 'immediate',
            'schedule_time': format_datetime(getattr(self, 'schedule_time', None)),
            'recurrence_interval_hours': getattr(self, 'recurrence_interval_hours', None),
            'recurrence_end_type': getattr(self, 'recurrence_end_type', None),
            'recurrence_max_runs': getattr(self, 'recurrence_max_runs', None),
            'recurrence_end_at': format_datetime(getattr(self, 'recurrence_end_at', None)),
            'recurrence_run_index': getattr(self, 'recurrence_run_index', None),
            'notes': self.notes,
            'created_at': format_datetime(self.created_at)
        }
