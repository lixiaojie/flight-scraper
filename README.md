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

## API 凭证

仓库中的 `scripts/config/scraper.config.json` 仅保存非敏感默认配置，`llmApiKey` 必须保持为空。Z.ai 功能使用 `ZAI_API_KEY` 环境变量；Docker Compose 将该变量传入后端与抓取服务。请通过本地安全的环境配置或秘密管理器提供值，不要将真实凭证写入源码、提交记录或日志。

如需文件配置，请使用仓库外的私有文件，并通过 `SCRAPER_CONFIG_PATH` 指定。`scripts/verify_zai_api.py` 会实际发送 API 请求；仅在确认使用的凭证与调用授权后手动运行。

如果凭证曾被提交，删除当前值不等于撤销凭证或清除 Git 历史：应在提供方撤销旧凭证，并在批准后单独处理历史副本。
