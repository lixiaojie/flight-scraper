"""
航班数据服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.models.flight_result import FlightResult
import logging

logger = logging.getLogger(__name__)

class FlightService:
    """航班数据服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_flight_results(self, flights: List[Dict[str, Any]], source: str = '12306') -> List[FlightResult]:
        """保存航班结果到数据库"""
        try:
            saved_flights = []
            
            for flight_data in flights:
                # 创建航班结果对象
                flight_result = FlightResult(
                    airline=flight_data.get('airline', ''),
                    flight_number=flight_data.get('flight_number', ''),
                    departure_time=flight_data.get('departure_time', ''),
                    departure_airport=flight_data.get('departure_airport', ''),
                    arrival_time=flight_data.get('arrival_time', ''),
                    arrival_airport=flight_data.get('arrival_airport', ''),
                    price=float(flight_data.get('price', 0)) if flight_data.get('price') else 0.0,
                    currency=flight_data.get('currency', 'CNY'),
                    source=source,
                    raw_data=str(flight_data),
                    notes=flight_data.get('notes', '')
                )
                
                self.db.add(flight_result)
                saved_flights.append(flight_result)
            
            self.db.commit()
            logger.info(f"成功保存 {len(saved_flights)} 条航班数据")
            return saved_flights
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存航班数据失败: {e}")
            raise e
    
    def get_flights_by_price_range(self, min_price: float = 0, max_price: float = 10000) -> List[FlightResult]:
        """根据价格范围查询航班"""
        try:
            flights = self.db.query(FlightResult).filter(
                FlightResult.price >= min_price,
                FlightResult.price <= max_price,
                FlightResult.status == 'active'
            ).order_by(asc(FlightResult.price)).all()
            
            return flights
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e
    
    def get_flights_by_airline(self, airline: str) -> List[FlightResult]:
        """根据航空公司查询航班"""
        try:
            flights = self.db.query(FlightResult).filter(
                FlightResult.airline.like(f'%{airline}%'),
                FlightResult.status == 'active'
            ).order_by(asc(FlightResult.price)).all()
            
            return flights
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e
    
    def get_flights_by_time_range(self, start_time: str, end_time: str) -> List[FlightResult]:
        """根据时间范围查询航班"""
        try:
            flights = self.db.query(FlightResult).filter(
                FlightResult.departure_time >= start_time,
                FlightResult.departure_time <= end_time,
                FlightResult.status == 'active'
            ).order_by(asc(FlightResult.price)).all()
            
            return flights
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e
    
    def get_latest_flights(self, limit: int = 50) -> List[FlightResult]:
        """获取最新的航班数据"""
        try:
            flights = self.db.query(FlightResult).filter(
                FlightResult.status == 'active'
            ).order_by(desc(FlightResult.scrape_time)).limit(limit).all()
            
            return flights
        except Exception as e:
            logger.error(f"查询最新航班数据失败: {e}")
            raise e
    
    def get_flights_by_date(self, date: datetime) -> List[FlightResult]:
        """根据日期查询航班"""
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            flights = self.db.query(FlightResult).filter(
                FlightResult.scrape_time >= start_date,
                FlightResult.scrape_time < end_date,
                FlightResult.status == 'active'
            ).order_by(asc(FlightResult.price)).all()
            
            return flights
        except Exception as e:
            logger.error(f"根据日期查询航班数据失败: {e}")
            raise e
    
    def get_flight_statistics(self) -> Dict[str, Any]:
        """获取航班统计信息"""
        try:
            total_flights = self.db.query(FlightResult).filter(
                FlightResult.status == 'active'
            ).count()
            
            min_price = self.db.query(FlightResult).filter(
                FlightResult.status == 'active'
            ).order_by(asc(FlightResult.price)).first()
            
            max_price = self.db.query(FlightResult).filter(
                FlightResult.status == 'active'
            ).order_by(desc(FlightResult.price)).first()
            
            avg_price = self.db.query(FlightResult).filter(
                FlightResult.status == 'active'
            ).with_entities(FlightResult.price).all()
            
            avg_price_value = sum([f.price for f in avg_price]) / len(avg_price) if avg_price else 0
            
            return {
                'total_flights': total_flights,
                'min_price': min_price.price if min_price else 0,
                'max_price': max_price.price if max_price else 0,
                'avg_price': round(avg_price_value, 2)
            }
        except Exception as e:
            logger.error(f"获取航班统计信息失败: {e}")
            raise e
    
    def delete_old_flights(self, days: int = 7) -> int:
        """删除旧的航班数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            old_flights = self.db.query(FlightResult).filter(
                FlightResult.scrape_time < cutoff_date
            ).all()
            
            count = len(old_flights)
            
            for flight in old_flights:
                self.db.delete(flight)
            
            self.db.commit()
            logger.info(f"删除了 {count} 条旧航班数据")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除旧航班数据失败: {e}")
            raise e
