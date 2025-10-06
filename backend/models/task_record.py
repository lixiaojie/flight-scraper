"""
抓取任务记录模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

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
    start_time = Column(DateTime, default=func.now(), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Integer, comment='执行时长(秒)')
    
    # 结果信息
    success = Column(Boolean, default=False, comment='是否成功')
    flights_count = Column(Integer, default=0, comment='抓取航班数量')
    error_message = Column(Text, comment='错误信息')
    
    # 配置信息
    source = Column(String(50), default='12306', comment='数据源')
    config = Column(Text, comment='任务配置')
    
    # 额外信息
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    
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
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_type': self.task_type,
            'status': self.status,
            'current_step': self.current_step,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'success': self.success,
            'flights_count': self.flights_count,
            'error_message': self.error_message,
            'source': self.source,
            'config': self.config,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
