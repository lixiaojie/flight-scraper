# Flight Scraper 项目

## 🎯 项目概述

Flight Scraper 是一个集成 Web 服务、Android 模拟器和 Appium 自动化采集的完整方案。

## 🏗️ 项目结构

```
flight-scraper/
├── backend/        # FastAPI 后端
├── frontend/       # React 前端
├── scripts/        # 抓取与运维脚本
├── docs/           # 项目文档
├── assets/         # 资源文件
└── docker-compose.yml
```

## 🚀 快速开始

### 1. 部署所有服务
```bash
./scripts/deploy.sh
```

### 2. 管理服务
```bash
# 启动服务
./scripts/manage.sh start

# 查看状态
./scripts/manage.sh status

# 查看日志
./scripts/manage.sh logs

# 停止服务
./scripts/manage.sh stop
```

## 🔧 服务说明

### Web 服务
- **Backend**: FastAPI 后端服务 (端口 8000)
- **Frontend**: React 前端服务 (端口 3000)
- **Nginx**: 反向代理 (端口 80/443)

### Android 服务
- **模拟器**: Android 模拟器 (VNC 端口 6080, ADB 端口 5555)
- **配置**: 支持多种 Android 版本和设备

### Appium 服务
- **自动化采集**: Appium 自动化采集服务 (端口 4723)
- **驱动**: UiAutomator2 驱动支持

## 📱 使用说明

### 1. 访问服务
- Web 应用: http://localhost:3000
- API 文档: http://localhost:8000/docs
- Android 模拟器: http://localhost:6080
- Appium 服务: http://localhost:4723

### 2. 启动抓取任务
```bash
# 使用默认配置启动抓取
./scripts/run_scraper.sh

# 仅运行航班抓取流程
./scripts/run_flight_scraper.sh
```

### 3. 开发调试
```bash
# 查看服务日志
docker-compose logs -f [service_name]

# 重启特定服务
docker-compose restart [service_name]

# 进入容器调试
docker-compose exec [service_name] bash
```

## 🛠️ 开发指南

### 添加新功能
1. 在对应的服务目录中开发
2. 更新 Docker 配置
3. 重新构建和部署

### 调试技巧
1. 使用 `docker-compose logs -f` 查看实时日志
2. 使用 `docker-compose exec` 进入容器调试
3. 使用 `docker-compose restart` 重启服务

## 📋 故障排除

### 常见问题
1. **端口冲突**: 检查端口是否被占用
2. **服务启动失败**: 查看日志排查问题
3. **网络连接**: 确保 Docker 网络正常

### 清理和重置
```bash
# 清理所有资源
./scripts/manage.sh clean

# 重新部署
./scripts/deploy.sh
```

## 📚 更多文档

- [Flight Scraper 指南](./Flight_Scraper_Guide.md)
- [航班结果系统指南](./Flight_Results_System_Guide.md)
- [开发环境指南](./DEVELOPMENT.md)
- [Docker 使用说明](./DOCKER_USAGE.md)
- [Appium 安装指南](./APPIUM_INSTALL_GUIDE.md)
- [Appium Inspector 指南](./Appium_Inspector_Guide.md)
- [城市选择优化说明](./CITY_SELECTION_IMPROVEMENT.md)
- [性能优化](./PERFORMANCE_OPTIMIZATION.md)
- [OCR 集成](./OCR_INTEGRATION_AND_OPTIMIZATION.md)
- 其他排障与总结类文档请见 `docs/` 目录
