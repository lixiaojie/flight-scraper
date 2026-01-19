# Flight Scraper 项目

## 🚀 快速开始

```bash
# 部署所有服务
./scripts/deploy.sh

# 管理服务
./scripts/manage.sh start    # 启动
./scripts/manage.sh stop     # 停止
./scripts/manage.sh status   # 状态
./scripts/manage.sh logs     # 日志
```

## 🧭 项目结构

```
flight-scraper/
├── backend/        # FastAPI 后端
├── frontend/       # React 前端
├── scripts/        # 抓取与运维脚本
├── docs/           # 项目文档
├── assets/         # 资源文件
└── docker-compose.yml
```

## 🧩 常用脚本

```bash
# 启动完整系统
./scripts/start_system.sh

# 启动抓取任务
./scripts/run_scraper.sh

# 仅启动航班抓取流程
./scripts/run_flight_scraper.sh
```

## 🔧 服务地址

- **Web 应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **Android 模拟器**: http://localhost:6080
- **Appium 服务**: http://localhost:4723

## 📖 详细文档

查看 [docs/README.md](./docs/README.md) 获取完整说明与指引。

## 🛠️ 开发

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart [service_name]
```
