"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Flight Data Scraping Tool"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./flight_scraper.db"
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Scraping Settings
    DEFAULT_QUERY_INTERVAL_MIN: int = 5
    DEFAULT_QUERY_INTERVAL_MAX: int = 15
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # OCR Settings
    TESSERACT_PATH: Optional[str] = None
    
    # Appium Settings
    APPIUM_SERVER_URL: str = "http://localhost:4723"
    
    # Selenium Settings
    SELENIUM_HEADLESS: bool = True
    SELENIUM_WINDOW_SIZE: str = "1920,1080"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    SCREENSHOTS_DIR: str = "screenshots"
    LOGS_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
