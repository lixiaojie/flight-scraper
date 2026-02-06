# Docker 使用说明

## 🚀 快速开始

### 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose down
```

### 重新构建服务
```bash
# 重新构建所有服务（使用缓存）
docker-compose build

# 重新构建特定服务
docker-compose build web

# 清理并重新构建（不使用缓存）
docker-compose build --no-cache
```

## 🔧 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| web | 8000 | 后端API服务 |
| frontend | 3000 | 前端Web界面 |
| appium | 4723 | Appium自动化服务 |
| android-emulator | 5555, 6080 | Android模拟器（仅开发模式） |

## 📋 常用命令


### 日志查看
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web

# 实时查看日志
docker-compose logs -f web
```

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec web bash
```

## 🌐 访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Appium服务**: http://localhost:4723
- **Android模拟器VNC**: http://localhost:6080 (仅开发模式)

## 🔍 故障排除

### 1. 构建失败
```bash
# 清理Docker缓存
docker system prune -f

# 清理构建缓存
docker builder prune -f

# 重新构建
docker-compose build --no-cache
```

### 2. 端口冲突
```bash
# 检查端口占用
lsof -i :8000
lsof -i :3000
lsof -i :4723

# 停止占用端口的进程
sudo kill -9 <PID>
```

### 3. 服务无法启动
```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs <service_name>

# 重启服务
docker-compose restart <service_name>
```

## 📁 文件结构

```
docker-compose.yml          # Docker Compose配置文件
```

## 🚀 性能优化

### 使用国内镜像源
所有Dockerfile已配置国内镜像源：
- **APT源**: 中科大镜像 (mirrors.ustc.edu.cn)
- **pip源**: 清华大学镜像 (pypi.tuna.tsinghua.edu.cn)
- **npm源**: 阿里云镜像 (registry.npmmirror.com)

### 构建缓存
- 支持BuildKit内联缓存（BUILDKIT_INLINE_CACHE=1）
- Docker自动使用构建缓存加速后续构建

## 📝 注意事项

1. **首次构建**：需要下载基础镜像，时间较长
2. **网络环境**：确保网络连接稳定
3. **资源要求**：建议至少4GB内存
4. **端口占用**：确保8000、3000、4723端口未被占用
