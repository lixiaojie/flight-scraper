"""
Flight data model for scraped flight information
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class FlightData(Base):
    """Flight data model for scraped flight information"""
    
    __tablename__ = "flight_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Flight details
    airline = Column(String(100), nullable=False)
    flight_number = Column(String(50), nullable=False)
    departure_airport = Column(String(10), nullable=False)
    arrival_airport = Column(String(10), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    duration = Column(String(20), nullable=True)  # e.g., "2h 30m"
    
    # Pricing
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    original_price = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)
    
    # Additional details
    stops = Column(Integer, default=0)
    aircraft_type = Column(String(50), nullable=True)
    cabin_class = Column(String(50), nullable=True)
    
    # Promotional offers
    promotional_offers = Column(Text, nullable=True)  # JSON string
    booking_url = Column(String(1000), nullable=True)
    
    # Source information
    source_platform = Column(String(100), nullable=False)
    source_account = Column(String(200), nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Data quality
    is_verified = Column(Boolean, default=False)
    confidence_score = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Relationships
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    task = relationship("Task", back_populates="flight_data")
    
    def __repr__(self):
        return f"<FlightData(id={self.id}, airline='{self.airline}', price={self.price}, source='{self.source_platform}')>"
