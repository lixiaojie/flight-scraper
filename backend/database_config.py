"""
统一数据库配置文件
所有数据库相关的配置都集中在这里管理
"""

import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 在Docker容器中，如果当前工作目录是/app，则使用/app作为根目录
if Path.cwd() == Path('/app'):
    PROJECT_ROOT = Path('/app')

# 数据库文件路径配置
DATABASE_FILE_NAME = "flight_scraper.db"

# 数据库文件位置选项
DATABASE_LOCATIONS = {
    "backend": PROJECT_ROOT / "backend" / DATABASE_FILE_NAME,
    "data": PROJECT_ROOT / "data" / DATABASE_FILE_NAME,
    "root": PROJECT_ROOT / DATABASE_FILE_NAME,
}

# 默认数据库位置
DEFAULT_DATABASE_LOCATION = "backend"

# 获取数据库文件路径


def get_database_path(location: str = None) -> Path:
    """获取数据库文件路径"""
    if location is None:
        location = os.getenv("DATABASE_LOCATION", DEFAULT_DATABASE_LOCATION)

    if location not in DATABASE_LOCATIONS:
        raise ValueError(
            f"无效的数据库位置: {location}. 可选值: {list(DATABASE_LOCATIONS.keys())}")

    return DATABASE_LOCATIONS[location]

# 获取数据库URL


def get_database_url(location: str = None) -> str:
    """获取数据库URL"""
    db_path = get_database_path(location)
    return f"sqlite:///{db_path}"

# 环境变量配置


def get_database_url_from_env() -> str:
    """从环境变量获取数据库URL，如果没有则使用默认配置"""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # 如果没有环境变量，使用默认配置
    return get_database_url()

# 数据库连接参数


def get_database_connect_args():
    """获取数据库连接参数"""
    return {"check_same_thread": False}


# 导出配置
DATABASE_URL = get_database_url_from_env()
DATABASE_PATH = get_database_path()
DATABASE_CONNECT_ARGS = get_database_connect_args()

# 打印配置信息（用于调试）
if __name__ == "__main__":
    print(f"数据库文件路径: {DATABASE_PATH}")
    print(f"数据库URL: {DATABASE_URL}")
    print(f"数据库文件是否存在: {DATABASE_PATH.exists()}")
