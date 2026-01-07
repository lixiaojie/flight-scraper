"""
航班数据服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.flight_result import FlightResult
import logging

logger = logging.getLogger(__name__)


class FlightService:
    """航班数据服务类"""

    def __init__(self, db: Session):
        self.db = db

    def save_flight_results(self,
                            flights: List[Dict[str,
                                               Any]],
                            source: str = '12306',
                            task_id: int = None,
                            scrape_time: datetime = None) -> List[FlightResult]:
        """保存航班结果到数据库"""
        try:
            saved_flights = []
            
            # 去重：基于航班号、出发时间、到达时间、价格等关键字段
            unique_flights = []
            seen_keys = set()
            
            for flight_data in flights:
                # 生成唯一键：航班号+出发时间+到达时间+价格
                flight_number = flight_data.get('flight_number', '')
                departure_time = flight_data.get('departure_time', '')
                arrival_time = flight_data.get('arrival_time', '')
                price = flight_data.get('price', 0)
                unique_key = f"{flight_number}_{departure_time}_{arrival_time}_{price}"
                
                if unique_key not in seen_keys:
                    unique_flights.append(flight_data)
                    seen_keys.add(unique_key)
                else:
                    logger.debug(f"跳过重复航班: {flight_number} {departure_time}-{arrival_time} {price}")
            
            if len(flights) != len(unique_flights):
                logger.info(f"去重: 原始 {len(flights)} 条, 去重后 {len(unique_flights)} 条")

            # 如果没有提供scrape_time，使用当前时间
            if scrape_time is None:
                scrape_time = datetime.now()

            for flight_data in unique_flights:
                # 创建航班结果对象
                flight_result = FlightResult(
                    airline=flight_data.get('airline', ''),
                    flight_number=flight_data.get('flight_number', ''),
                    is_shared_flight=flight_data.get('is_shared_flight'),
                    aircraft_type=flight_data.get('aircraft_type'),
                    departure_date=flight_data.get('departure_date'),
                    departure_time=flight_data.get('departure_time', ''),
                    departure_airport=flight_data.get('departure_airport', ''),
                    departure_city=flight_data.get('departure_city'),
                    arrival_time=flight_data.get('arrival_time', ''),
                    arrival_airport=flight_data.get('arrival_airport', ''),
                    arrival_city=flight_data.get('arrival_city'),
                    departure_terminal=flight_data.get('departure_terminal'),
                    arrival_terminal=flight_data.get('arrival_terminal'),
                    flight_duration=flight_data.get('flight_duration'),
                    has_stopover=flight_data.get('has_stopover'),
                    stopover_city=flight_data.get('stopover_city'),
                    stopover_airport=flight_data.get('stopover_airport'),
                    price=float(
                        flight_data.get(
                            'price',
                            0)) if flight_data.get('price') else 0.0,
                    currency=flight_data.get('currency', 'CNY'),
                    cabin_class=flight_data.get('cabin_class'),
                    discount_rate=flight_data.get('discount_rate'),
                    original_price=float(
                        flight_data.get(
                            'original_price',
                            0)) if flight_data.get('original_price') else None,
                    task_id=task_id,  # 确保task_id被正确设置
                    scrape_time=scrape_time,  # 使用传入的scrape_time
                    source=source,
                    raw_data=str(flight_data),
                    notes=flight_data.get('notes', '')
                )
                
                # 验证task_id是否正确设置
                if task_id and flight_result.task_id != task_id:
                    logger.warning(f"⚠️ 航班 {flight_result.flight_number} 的 task_id 设置异常: 期望 {task_id}, 实际 {flight_result.task_id}")
                    flight_result.task_id = task_id  # 强制设置

                self.db.add(flight_result)
                saved_flights.append(flight_result)

            self.db.commit()
            logger.info(f"成功保存 {len(saved_flights)} 条航班数据")
            return saved_flights

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存航班数据失败: {e}")
            raise e

    def get_flights_by_price_range(
            self,
            min_price: float = 0,
            max_price: float = 10000,
            sort_by: str = "price") -> List[FlightResult]:
        """根据价格范围查询航班"""
        try:
            query = self.db.query(FlightResult).filter(
                FlightResult.price >= min_price,
                FlightResult.price <= max_price,
                FlightResult.status == 'active'
            )

            if sort_by == "time":
                query = query.order_by(asc(FlightResult.departure_time))
            else:
                query = query.order_by(asc(FlightResult.price))

            return query.all()
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e

    def get_flights_by_airline(
            self,
            airline: str,
            sort_by: str = "price") -> List[FlightResult]:
        """根据航空公司查询航班"""
        try:
            query = self.db.query(FlightResult).filter(
                FlightResult.airline.like(f'%{airline}%'),
                FlightResult.status == 'active'
            )

            if sort_by == "time":
                query = query.order_by(asc(FlightResult.departure_time))
            else:
                query = query.order_by(asc(FlightResult.price))

            return query.all()
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e

    def get_flights_by_time_range(
            self,
            start_time: str,
            end_time: str) -> List[FlightResult]:
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
            start_date = date.replace(
                hour=0, minute=0, second=0, microsecond=0)
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

            avg_price_value = sum([f.price for f in avg_price]) / \
                len(avg_price) if avg_price else 0

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

    def get_flights_grouped_by_task(
            self,
            limit: int = 50,
            sort_by: str = "price",
            flight_number: str = None,
            departure_city: str = None,
            arrival_city: str = None,
            task_id: int = None) -> List[FlightResult]:
        """按任务分组获取航班数据，最近的任务在前，同一任务内按指定方式排序"""
        try:
            logger.info(f"🔍 查询航班: task_id={task_id}, flight_number={flight_number}, departure_city={departure_city}, arrival_city={arrival_city}, limit={limit}, sort_by={sort_by}")
            # 如果指定了task_id，只查询该任务的航班；否则查询所有有task_id的航班
            if task_id is not None:
                logger.info(f"🔍 按 task_id={task_id} 过滤航班")
                flights = self.db.query(FlightResult).filter(
                    FlightResult.status == 'active',
                    FlightResult.task_id == task_id
                )
            else:
                # 查询所有活跃的航班（包括有task_id和没有task_id的）
                flights = self.db.query(FlightResult).filter(
                    FlightResult.status == 'active'
                )

            # 应用其他筛选条件
            if flight_number:
                flights = flights.filter(
                    FlightResult.flight_number.like(
                        f'%{flight_number}%'))
            if departure_city:
                flights = flights.filter(
                    FlightResult.departure_city.like(
                        f'%{departure_city}%'))
            if arrival_city:
                flights = flights.filter(
                    FlightResult.arrival_city.like(
                        f'%{arrival_city}%'))

            # 排序：如果指定了task_id，只按价格或时间排序；否则先按task_id排序，再按价格或时间排序
            if task_id is not None:
                # 如果指定了task_id，只按价格或时间排序
                if sort_by == "time":
                    flights = flights.order_by(
                        asc(FlightResult.departure_time))
                else:
                    flights = flights.order_by(asc(FlightResult.price))
            else:
                # 否则先按task_id排序，再按价格或时间排序
                flights = flights.order_by(desc(FlightResult.task_id))
                if sort_by == "time":
                    flights = flights.order_by(
                        desc(
                            FlightResult.task_id), asc(
                            FlightResult.departure_time))
                else:
                    flights = flights.order_by(
                        desc(
                            FlightResult.task_id), asc(
                            FlightResult.price))

            result = flights.limit(limit).all()
            logger.info(f"✅ 查询完成，找到 {len(result)} 条航班记录")
            return result
        except Exception as e:
            logger.error(f"查询航班数据失败: {e}")
            raise e
