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

## 🔧 服务地址

- **Web 应用**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **Android 模拟器**: http://localhost:6080
- **Appium 服务**: http://localhost:4723

## 📖 详细文档

查看 [docs/README.md](./docs/README.md) 获取完整文档。

## 🛠️ 开发

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart [service_name]
```
