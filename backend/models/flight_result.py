"""
航班结果数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class FlightResult(Base):
    """航班结果模型"""
    __tablename__ = 'flight_results'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 航班基本信息
    airline = Column(String(100), nullable=False, comment='航空公司')
    flight_number = Column(String(20), nullable=False, comment='航班号')
    is_shared_flight = Column(String(10), nullable=True, comment='是否共享航班')
    aircraft_type = Column(String(50), nullable=True, comment='飞机型号')
    departure_date = Column(String(20), nullable=True, comment='出发日期')
    departure_time = Column(String(10), nullable=False, comment='起飞时间')
    departure_airport = Column(String(50), nullable=False, comment='起飞机场')
    departure_city = Column(String(50), nullable=True, comment='出发城市')
    arrival_time = Column(String(10), nullable=False, comment='落地时间')
    arrival_airport = Column(String(50), nullable=False, comment='落地机场')
    arrival_city = Column(String(50), nullable=True, comment='到达城市')
    # 航站楼信息
    departure_terminal = Column(String(20), nullable=True, comment='出发航站楼')
    arrival_terminal = Column(String(20), nullable=True, comment='到达航站楼')
    flight_duration = Column(String(20), nullable=True, comment='飞行时长')

    # 经停信息
    has_stopover = Column(String(10), nullable=True, comment='是否经停')
    stopover_city = Column(String(50), nullable=True, comment='经停城市')
    stopover_airport = Column(String(50), nullable=True, comment='经停机场')

    # 价格信息
    price = Column(Float, nullable=False, comment='最低价格')
    currency = Column(String(10), default='CNY', comment='货币单位')
    cabin_class = Column(String(20), nullable=True, comment='舱位等级')
    discount_rate = Column(String(20), nullable=True, comment='折扣率')
    original_price = Column(Float, nullable=True, comment='原价')

    # 抓取信息
    task_id = Column(Integer, nullable=True, comment='关联的任务ID')
    scrape_time = Column(DateTime, default=func.now(), comment='抓取时间')
    source = Column(String(50), default='12306', comment='数据源')
    status = Column(String(20), default='active', comment='状态')

    # 额外信息
    raw_data = Column(Text, comment='原始数据')
    notes = Column(Text, comment='备注')
    field_sources = Column(Text, nullable=True, comment='字段来源标识（JSON格式，标识哪些字段来自OCR）')

    # 索引
    __table_args__ = (
        Index('idx_flight_number', 'flight_number'),
        Index('idx_departure_time', 'departure_time'),
        Index('idx_price', 'price'),
        Index('idx_scrape_time', 'scrape_time'),
        Index('idx_airline', 'airline'),
        Index('idx_task_id', 'task_id'),
    )

    def __repr__(self):
        return f"<FlightResult(flight_number='{self.flight_number}', price={self.price})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'airline': self.airline,
            'flight_number': self.flight_number,
            'is_shared_flight': self.is_shared_flight,
            'aircraft_type': self.aircraft_type,
            'departure_date': self.departure_date,
            'departure_time': self.departure_time,
            'departure_airport': self.departure_airport,
            'departure_city': self.departure_city,
            'arrival_time': self.arrival_time,
            'arrival_airport': self.arrival_airport,
            'arrival_city': self.arrival_city,
            'departure_terminal': self.departure_terminal,
            'arrival_terminal': self.arrival_terminal,
            'flight_duration': self.flight_duration,
            'has_stopover': self.has_stopover,
            'stopover_city': self.stopover_city,
            'stopover_airport': self.stopover_airport,
            'price': self.price,
            'currency': self.currency,
            'cabin_class': self.cabin_class,
            'discount_rate': self.discount_rate,
            'original_price': self.original_price,
            'task_id': self.task_id,
            'scrape_time': self.scrape_time.isoformat() if self.scrape_time else None,
            'source': self.source,
            'status': self.status,
            'notes': self.notes,
            'field_sources': getattr(self, 'field_sources', None)}
