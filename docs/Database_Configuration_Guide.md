# 数据库配置统一指南

## 概述

本项目已将所有数据库文件引用统一到 `backend/database_config.py` 文件中，确保所有组件使用相同的数据库配置。

## 统一配置文件

### `backend/database_config.py`

这是所有数据库配置的中央文件，包含：

- 数据库文件路径配置
- 数据库URL生成
- 环境变量处理
- 连接参数配置

## 数据库位置选项

```python
DATABASE_LOCATIONS = {
    "backend": PROJECT_ROOT / "backend" / "flight_scraper.db",
    "data": PROJECT_ROOT / "data" / "flight_scraper.db", 
    "root": PROJECT_ROOT / "flight_scraper.db",
}
```

## 环境变量配置

### 开发环境
```bash
DATABASE_LOCATION=backend
DATABASE_URL=sqlite:///./backend/flight_scraper.db
```

### Docker环境
```bash
DATABASE_LOCATION=root
DATABASE_URL=sqlite:///./flight_scraper.db
```

## 使用方式

### 1. 在Python代码中使用

```python
from database_config import DATABASE_URL, DATABASE_PATH, DATABASE_CONNECT_ARGS

# 使用数据库URL
engine = create_engine(DATABASE_URL, connect_args=DATABASE_CONNECT_ARGS)
```

### 2. 在迁移脚本中使用

```python
from database_config import DATABASE_URL

def run_migration():
    engine = create_engine(DATABASE_URL)
    # ... 迁移逻辑
```

### 3. 在Docker Compose中配置

```yaml
environment:
  - DATABASE_URL=sqlite:///./flight_scraper.db
  - DATABASE_LOCATION=root
```

## 已更新的文件

### 后端文件
- `backend/core/database.py` - 使用统一配置
- `backend/core/config.py` - 使用统一配置
- `backend/init_database.py` - 使用统一配置
- `backend/init_admin.py` - 使用统一配置

### 迁移脚本
- `backend/migrate_add_airline.py`
- `backend/migrate_add_task_id.py`
- `backend/migrate_add_terminals.py`
- `backend/migrate_add_current_step.py`
- `backend/migrate_expand_flight_fields.py`

### Docker配置
- `docker-compose.yml` - 生产环境配置
- `docker-compose.dev.yml` - 开发环境配置
- `docker-compose.fast.yml` - 快速环境配置

### 工具脚本
- `scripts/cleanup.py` - 使用统一配置清理数据库

## 配置验证

### 本地环境验证
```bash
cd backend
python database_config.py
```

### Docker环境验证
```bash
docker-compose exec web python3 -c "
import sys
sys.path.insert(0, '/app')
from database_config import DATABASE_URL, DATABASE_PATH
print(f'数据库URL: {DATABASE_URL}')
print(f'数据库路径: {DATABASE_PATH}')
print(f'数据库文件是否存在: {DATABASE_PATH.exists()}')
"
```

## 优势

1. **统一管理**: 所有数据库配置集中在一个文件中
2. **环境适配**: 支持不同环境使用不同的数据库位置
3. **易于维护**: 修改数据库配置只需要更新一个文件
4. **类型安全**: 提供类型提示和验证
5. **向后兼容**: 支持现有的环境变量配置

## 注意事项

1. 确保所有新文件都使用 `database_config.py` 中的配置
2. 不要直接硬编码数据库路径
3. 使用环境变量 `DATABASE_LOCATION` 来指定数据库位置
4. 在Docker环境中，数据库文件位置可能因挂载配置而异
