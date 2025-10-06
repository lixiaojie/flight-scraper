# Flight Scraper 项目

## 🎯 项目概述

Flight Scraper 是一个集成了 Web 服务、Android 模拟器和 Appium 自动化测试的完整解决方案。

## 🏗️ 项目结构

```
flight-scraper/
├── services/           # 核心服务
│   ├── web/           # Web 服务 (Backend + Frontend)
│   ├── android/       # Android 服务配置
│   └── appium/        # Appium 自动化测试
├── docker/            # Docker 配置文件
├── scripts/           # 部署和管理脚本
├── docs/              # 项目文档
├── assets/            # 资源文件
└── docker-compose.yml # Docker Compose 配置
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
- **自动化测试**: Appium 自动化测试服务 (端口 4723)
- **驱动**: UiAutomator2 驱动支持
- **脚本**: 完整的自动化测试脚本

## 📱 使用说明

### 1. 访问服务
- Web 应用: http://localhost:3000
- API 文档: http://localhost:8000/docs
- Android 模拟器: http://localhost:6080
- Appium 服务: http://localhost:4723

### 2. 自动化测试
```bash
# 进入 Appium 容器
docker-compose exec appium bash

# 运行测试脚本
python3 appium_automation_script.py
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

- [登录问题修复总结](./Login_Issue_Fix_Summary.md)
- [422错误修复总结](./422_Error_Fix_Summary.md)
- [系统优化总结](./System_Optimization_Summary.md)
- [最终登录修复总结](./Final_Login_Fix_Summary.md)
- [最终422错误修复总结](./Final_422_Error_Fix_Summary.md)
- [航班结果系统指南](./Flight_Results_System_Guide.md)
- [最终系统状态总结](./Final_System_Status_Summary.md)
