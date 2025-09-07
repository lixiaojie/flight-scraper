"""
Flight comparison and price analysis service
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.flight_data import FlightData
from app.models.task import Task
from loguru import logger


class ComparisonService:
    """Service for comparing flights and finding best deals"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_best_deals(self, task_id: int) -> Dict[str, Any]:
        """
        Find the best flight deals for a given task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary containing best deals and analysis
        """
        try:
            # Get all flights for the task
            flights = self.db.query(FlightData).filter(
                FlightData.task_id == task_id
            ).all()
            
            if not flights:
                return {
                    'best_deal': None,
                    'price_analysis': {},
                    'platform_comparison': {},
                    'total_flights': 0
                }
            
            # Find best deal (lowest price)
            best_deal = self._find_lowest_price_flight(flights)
            
            # Price analysis
            price_analysis = self._analyze_prices(flights)
            
            # Platform comparison
            platform_comparison = self._compare_platforms(flights)
            
            # Airline analysis
            airline_analysis = self._analyze_airlines(flights)
            
            # Time analysis
            time_analysis = self._analyze_times(flights)
            
            return {
                'best_deal': best_deal,
                'price_analysis': price_analysis,
                'platform_comparison': platform_comparison,
                'airline_analysis': airline_analysis,
                'time_analysis': time_analysis,
                'total_flights': len(flights),
                'analysis_timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error finding best deals: {str(e)}")
            return {'error': str(e)}
    
    def _find_lowest_price_flight(self, flights: List[FlightData]) -> Optional[Dict[str, Any]]:
        """Find the flight with the lowest price"""
        if not flights:
            return None
        
        lowest_price_flight = min(flights, key=lambda f: f.price)
        
        return {
            'id': lowest_price_flight.id,
            'airline': lowest_price_flight.airline,
            'flight_number': lowest_price_flight.flight_number,
            'departure_time': lowest_price_flight.departure_time,
            'arrival_time': lowest_price_flight.arrival_time,
            'price': lowest_price_flight.price,
            'currency': lowest_price_flight.currency,
            'stops': lowest_price_flight.stops,
            'duration': lowest_price_flight.duration,
            'source_platform': lowest_price_flight.source_platform,
            'confidence_score': lowest_price_flight.confidence_score
        }
    
    def _analyze_prices(self, flights: List[FlightData]) -> Dict[str, Any]:
        """Analyze price distribution and statistics"""
        if not flights:
            return {}
        
        prices = [f.price for f in flights if f.price]
        
        if not prices:
            return {}
        
        prices.sort()
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'average_price': sum(prices) / len(prices),
            'median_price': prices[len(prices) // 2],
            'price_range': max(prices) - min(prices),
            'price_quartiles': {
                'q1': prices[len(prices) // 4],
                'q2': prices[len(prices) // 2],
                'q3': prices[3 * len(prices) // 4]
            },
            'total_flights': len(prices)
        }
    
    def _compare_platforms(self, flights: List[FlightData]) -> Dict[str, Any]:
        """Compare prices and availability across platforms"""
        platform_stats = {}
        
        for flight in flights:
            platform = flight.source_platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    'flights': [],
                    'min_price': float('inf'),
                    'max_price': 0,
                    'total_price': 0,
                    'count': 0
                }
            
            platform_stats[platform]['flights'].append(flight)
            platform_stats[platform]['min_price'] = min(
                platform_stats[platform]['min_price'], 
                flight.price
            )
            platform_stats[platform]['max_price'] = max(
                platform_stats[platform]['max_price'], 
                flight.price
            )
            platform_stats[platform]['total_price'] += flight.price
            platform_stats[platform]['count'] += 1
        
        # Calculate averages and rankings
        for platform, stats in platform_stats.items():
            stats['average_price'] = stats['total_price'] / stats['count']
            stats['price_range'] = stats['max_price'] - stats['min_price']
        
        # Sort platforms by average price
        sorted_platforms = sorted(
            platform_stats.items(),
            key=lambda x: x[1]['average_price']
        )
        
        return {
            'platforms': dict(sorted_platforms),
            'best_platform': sorted_platforms[0][0] if sorted_platforms else None,
            'platform_count': len(platform_stats)
        }
    
    def _analyze_airlines(self, flights: List[FlightData]) -> Dict[str, Any]:
        """Analyze airline performance and pricing"""
        airline_stats = {}
        
        for flight in flights:
            airline = flight.airline
            if not airline:
                continue
                
            if airline not in airline_stats:
                airline_stats[airline] = {
                    'flights': [],
                    'min_price': float('inf'),
                    'max_price': 0,
                    'total_price': 0,
                    'count': 0,
                    'total_stops': 0
                }
            
            airline_stats[airline]['flights'].append(flight)
            airline_stats[airline]['min_price'] = min(
                airline_stats[airline]['min_price'], 
                flight.price
            )
            airline_stats[airline]['max_price'] = max(
                airline_stats[airline]['max_price'], 
                flight.price
            )
            airline_stats[airline]['total_price'] += flight.price
            airline_stats[airline]['count'] += 1
            airline_stats[airline]['total_stops'] += flight.stops or 0
        
        # Calculate averages
        for airline, stats in airline_stats.items():
            stats['average_price'] = stats['total_price'] / stats['count']
            stats['average_stops'] = stats['total_stops'] / stats['count']
            stats['price_range'] = stats['max_price'] - stats['min_price']
        
        # Sort by average price
        sorted_airlines = sorted(
            airline_stats.items(),
            key=lambda x: x[1]['average_price']
        )
        
        return {
            'airlines': dict(sorted_airlines),
            'cheapest_airline': sorted_airlines[0][0] if sorted_airlines else None,
            'airline_count': len(airline_stats)
        }
    
    def _analyze_times(self, flights: List[FlightData]) -> Dict[str, Any]:
        """Analyze departure and arrival times"""
        if not flights:
            return {}
        
        departure_times = []
        arrival_times = []
        durations = []
        
        for flight in flights:
            if flight.departure_time:
                departure_times.append(flight.departure_time)
            if flight.arrival_time:
                arrival_times.append(flight.arrival_time)
            if flight.duration:
                # Parse duration (e.g., "2h 30m")
                duration_minutes = self._parse_duration_to_minutes(flight.duration)
                if duration_minutes:
                    durations.append(duration_minutes)
        
        return {
            'departure_times': {
                'earliest': min(departure_times) if departure_times else None,
                'latest': max(departure_times) if departure_times else None,
                'count': len(departure_times)
            },
            'arrival_times': {
                'earliest': min(arrival_times) if arrival_times else None,
                'latest': max(arrival_times) if arrival_times else None,
                'count': len(arrival_times)
            },
            'durations': {
                'shortest': min(durations) if durations else None,
                'longest': max(durations) if durations else None,
                'average': sum(durations) / len(durations) if durations else None,
                'count': len(durations)
            }
        }
    
    def _parse_duration_to_minutes(self, duration_str: str) -> Optional[int]:
        """Parse duration string to minutes"""
        if not duration_str:
            return None
        
        import re
        
        # Match patterns like "2h 30m", "2h", "30m", "2:30"
        hour_match = re.search(r'(\d+)h', duration_str)
        minute_match = re.search(r'(\d+)m', duration_str)
        colon_match = re.search(r'(\d+):(\d+)', duration_str)
        
        total_minutes = 0
        
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        
        if minute_match:
            total_minutes += int(minute_match.group(1))
        
        if colon_match:
            total_minutes += int(colon_match.group(1)) * 60 + int(colon_match.group(2))
        
        return total_minutes if total_minutes > 0 else None
    
    def get_price_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get price trends over time"""
        try:
            # Get flights from the last N days
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Group by date and get price statistics
            price_trends = self.db.query(
                func.date(FlightData.scraped_at).label('date'),
                func.avg(FlightData.price).label('avg_price'),
                func.min(FlightData.price).label('min_price'),
                func.max(FlightData.price).label('max_price'),
                func.count(FlightData.id).label('flight_count')
            ).filter(
                FlightData.scraped_at >= start_date
            ).group_by(
                func.date(FlightData.scraped_at)
            ).order_by('date').all()
            
            return {
                'trends': [
                    {
                        'date': trend.date.isoformat(),
                        'average_price': float(trend.avg_price),
                        'minimum_price': float(trend.min_price),
                        'maximum_price': float(trend.max_price),
                        'flight_count': trend.flight_count
                    }
                    for trend in price_trends
                ],
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting price trends: {str(e)}")
            return {'error': str(e)}
    
    def find_similar_routes(self, departure_city: str, arrival_city: str, days: int = 30) -> Dict[str, Any]:
        """Find similar routes and their historical prices"""
        try:
            # Get flights for similar routes in the last N days
            start_date = datetime.utcnow() - timedelta(days=days)
            
            similar_flights = self.db.query(FlightData).join(Task).filter(
                and_(
                    Task.departure_city.ilike(f'%{departure_city}%'),
                    Task.arrival_city.ilike(f'%{arrival_city}%'),
                    FlightData.scraped_at >= start_date
                )
            ).all()
            
            if not similar_flights:
                return {'message': 'No similar routes found'}
            
            # Analyze similar routes
            prices = [f.price for f in similar_flights if f.price]
            
            return {
                'route': f"{departure_city} → {arrival_city}",
                'historical_data': {
                    'min_price': min(prices) if prices else None,
                    'max_price': max(prices) if prices else None,
                    'average_price': sum(prices) / len(prices) if prices else None,
                    'flight_count': len(similar_flights),
                    'period_days': days
                },
                'recent_flights': [
                    {
                        'date': f.scraped_at.isoformat(),
                        'price': f.price,
                        'airline': f.airline,
                        'platform': f.source_platform
                    }
                    for f in similar_flights[-10:]  # Last 10 flights
                ]
            }
            
        except Exception as e:
            logger.error(f"Error finding similar routes: {str(e)}")
            return {'error': str(e)}
