# 航班结果系统使用指南

## 🎯 系统概述

这是一个完整的航班信息抓取、存储和展示系统，包含：
- **后端API**: FastAPI + SQLAlchemy + SQLite
- **前端界面**: React + TypeScript + Tailwind CSS
- **数据抓取**: Appium自动化 + 12306应用
- **数据库**: SQLite（可扩展为PostgreSQL/MySQL）

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   后端API       │    │   数据库        │
│   React App     │◄──►│   FastAPI       │◄──►│   SQLite        │
│   - 航班展示    │    │   - 数据接口    │    │   - 航班数据    │
│   - 搜索筛选    │    │   - 统计分析    │    │   - 索引优化    │
│   - 价格排序    │    │   - 批量保存    │    │   - 数据清理    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   数据抓取      │
                    │   Appium        │
                    │   - 12306应用   │
                    │   - 自动化流程  │
                    │   - 数据解析    │
                    └─────────────────┘
```

## 🚀 快速开始

### 1. 环境准备

#### 启动后端服务
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install fastapi uvicorn sqlalchemy

# 初始化数据库
python init_database.py

# 启动API服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 启动前端服务
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 启动Appium服务
```bash
# 启动Appium服务器
./scripts/start_appium_inspector_fixed.sh
```

### 2. 运行数据抓取

```bash
# 运行增强版抓取脚本
source flight_scraper_env/bin/activate && python3 scripts/enhanced_flight_scraper.py
```

### 3. 查看结果

访问前端页面: http://localhost:3000/flight-results

## 📊 功能特性

### 前端功能
- **📈 统计仪表板**: 总航班数、价格范围、平均价格
- **🔍 智能搜索**: 按价格、航空公司、时间筛选
- **📋 航班列表**: 按价格从低到高排序显示
- **🎨 美观界面**: 现代化UI设计，响应式布局
- **🔄 实时刷新**: 自动更新最新数据

### 后端功能
- **💾 数据存储**: 自动保存航班信息到数据库
- **📊 统计分析**: 提供价格统计和趋势分析
- **🔍 查询接口**: 支持多种查询条件
- **🧹 数据清理**: 自动清理过期数据
- **📈 批量操作**: 支持批量保存和删除

### 抓取功能
- **🔄 应用重启**: 确保从首页开始抓取
- **🔄 循环重试**: 智能重试机制提高成功率
- **🔄 页面刷新**: 自动刷新解决加载问题
- **⚡ 性能优化**: 等待时间优化提升速度
- **📸 错误处理**: 自动截图和日志记录

## 🗄️ 数据库设计

### 航班结果表 (flight_results)
```sql
CREATE TABLE flight_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline VARCHAR(100) NOT NULL,           -- 航空公司
    flight_number VARCHAR(20) NOT NULL,      -- 航班号
    departure_time VARCHAR(10) NOT NULL,     -- 起飞时间
    departure_airport VARCHAR(10) NOT NULL,  -- 起飞机场
    arrival_time VARCHAR(10) NOT NULL,       -- 落地时间
    arrival_airport VARCHAR(10) NOT NULL,    -- 落地机场
    price FLOAT NOT NULL,                   -- 价格
    currency VARCHAR(10) DEFAULT 'CNY',     -- 货币单位
    scrape_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 抓取时间
    source VARCHAR(50) DEFAULT '12306',     -- 数据源
    status VARCHAR(20) DEFAULT 'active',    -- 状态
    raw_data TEXT,                          -- 原始数据
    notes TEXT                              -- 备注
);
```

### 索引优化
- `idx_flight_number`: 航班号索引
- `idx_departure_time`: 起飞时间索引
- `idx_price`: 价格索引
- `idx_scrape_time`: 抓取时间索引
- `idx_airline`: 航空公司索引

## 🔌 API接口

### 航班查询接口
```http
GET /api/flights
GET /api/flights?min_price=100&max_price=1000
GET /api/flights?airline=中国国际航空
GET /api/flights?limit=50
```

### 统计信息接口
```http
GET /api/flights/statistics
```

### 批量保存接口
```http
POST /api/flights/batch-save
Content-Type: application/json

{
  "flights": [
    {
      "airline": "中国国际航空",
      "flight_number": "CA1234",
      "departure_time": "08:30",
      "departure_airport": "PEK",
      "arrival_time": "14:25",
      "arrival_airport": "SHA",
      "price": 580.0,
      "currency": "CNY"
    }
  ],
  "source": "12306"
}
```

### 数据清理接口
```http
DELETE /api/flights/cleanup?days=7
```

## 🎨 前端界面

### 主要组件
- **统计卡片**: 显示总航班数、价格范围、平均价格
- **搜索筛选**: 价格范围、航空公司、显示数量
- **航班列表**: 卡片式展示，包含航班信息、价格、时间
- **响应式设计**: 支持桌面和移动设备

### 界面特性
- **价格排序**: 自动按价格从低到高排序
- **航空公司标识**: 不同颜色标识不同航空公司
- **时间显示**: 清晰的起飞和落地时间
- **价格高亮**: 突出显示价格信息
- **实时更新**: 显示抓取时间

## 🔧 配置说明

### 后端配置
```python
# backend/core/config.py
DATABASE_URL = "sqlite:///./flight_scraper.db"
API_HOST = "0.0.0.0"
API_PORT = 8000
```

### 前端配置
```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = 'http://localhost:8000/api';
```

### 抓取配置
```python
# scripts/enhanced_flight_scraper.py
API_BASE_URL = "http://localhost:8000"
MAX_ATTEMPTS = 5  # 最大重试次数
WAIT_TIME = 2     # 等待时间（秒）
```

## 📈 性能优化

### 数据库优化
- **索引优化**: 为常用查询字段创建索引
- **数据清理**: 定期清理过期数据
- **批量操作**: 使用批量插入提高性能

### 前端优化
- **虚拟滚动**: 大量数据时使用虚拟滚动
- **缓存机制**: 缓存API响应减少请求
- **懒加载**: 按需加载组件和数据

### 抓取优化
- **并发控制**: 控制并发抓取数量
- **错误重试**: 智能重试机制
- **资源管理**: 及时释放资源

## 🚨 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库文件
ls -la flight_scraper.db

# 重新初始化数据库
python backend/init_database.py
```

#### 2. API服务无法访问
```bash
# 检查服务状态
curl http://localhost:8000/api/flights/statistics

# 重启服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. 前端页面空白
```bash
# 检查前端服务
npm run dev

# 检查API连接
curl http://localhost:8000/api/flights
```

#### 4. 抓取失败
```bash
# 检查Appium服务
curl http://localhost:4723/status

# 检查Android设备
adb devices

# 查看抓取日志
tail -f enhanced_flight_scraper_error_*.xml
```

## 📚 相关文档

- **增强步骤指南**: `docs/Enhanced_Steps_Guide.md`
- **API修复指南**: `docs/Appium_API_Fixes.md`
- **Inspector指南**: `docs/Appium_Inspector_Fix_Guide.md`
- **使用指南**: `docs/Flight_Scraper_Guide.md`

## 🎉 总结

这个航班结果系统提供了完整的解决方案：
- **数据抓取**: 自动化抓取12306航班信息
- **数据存储**: 结构化存储到数据库
- **数据展示**: 美观的前端界面展示
- **数据分析**: 统计分析和趋势预测

系统具有高可用性、高性能和易扩展的特点，可以满足航班信息查询和分析的需求。
