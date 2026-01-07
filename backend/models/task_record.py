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
            'notes': self.notes,
            'created_at': format_datetime(self.created_at)
        }
