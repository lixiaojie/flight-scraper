"""
应用配置
"""

import os
from typing import Optional

# 数据库配置
from database_config import DATABASE_URL

# 设置时区
import os
os.environ['TZ'] = 'Asia/Shanghai'

# JWT配置
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# 应用配置
APP_NAME = "航班信息API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "12306航班信息抓取和查询API"

# 抓取配置
SCRAPER_CONFIG = {
    "max_retries": 5,
    "wait_time": 2,
    "timeout": 30
}
