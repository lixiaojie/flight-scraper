# 开发环境快速指南

## 🚀 快速开始

### 方式1: 快速开发模式（推荐）
使用Docker构建缓存，适合日常开发：

```bash
# 快速启动
./scripts/quick_dev_start.sh

# 或手动启动
docker-compose -f docker-compose.fast.yml up -d
```

### 方式2: 标准生产模式
使用标准Docker构建：

```bash
docker-compose up -d
```

### 方式3: 高级开发模式（实验性）
使用本地依赖缓存，需要先设置：

```bash
# 首次设置（可能遇到依赖编译问题）
./scripts/setup_dev_cache.sh

# 启动开发环境
./scripts/dev_start.sh
```

## 📦 依赖缓存说明

### 前端依赖缓存
- **位置**: `./cache/node_modules`
- **用途**: 缓存npm依赖包，避免重复下载
- **更新**: 当package.json变化时运行 `./scripts/update_cache.sh`

### 后端依赖缓存
- **位置**: `./cache/python_venv`
- **用途**: 缓存Python虚拟环境和依赖包
- **更新**: 当requirements.txt变化时运行 `./scripts/update_cache.sh`

## 🔧 开发工作流

### 1. 代码更改
```bash
# 前端代码更改后，自动热重载
# 后端代码更改后，自动重启服务
```

### 2. 依赖更新
```bash
# 更新前端依赖
cd frontend
npm install
cd ..

# 更新后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 更新缓存
./scripts/update_cache.sh
```

### 3. 服务管理
```bash
# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.dev.yml restart frontend

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

## 🎯 性能优化

### 构建速度对比
- **标准模式**: 每次构建都下载依赖，耗时 2-5 分钟
- **开发模式**: 使用缓存，首次 2-3 分钟，后续 30-60 秒

### 缓存策略
1. **首次运行**: 下载并缓存所有依赖
2. **代码更改**: 只重新构建应用代码，不重新下载依赖
3. **依赖更改**: 运行更新脚本重新缓存依赖

## 🛠️ 故障排除

### 缓存问题
```bash
# 清理所有缓存
rm -rf ./cache
./scripts/setup_dev_cache.sh
```

### 依赖冲突
```bash
# 重新安装依赖
./scripts/update_cache.sh
```

### 服务问题
```bash
# 完全重启
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

## 📁 文件结构

```
flight-scraper/
├── cache/                    # 依赖缓存目录
│   ├── node_modules/        # 前端依赖缓存
│   └── python_venv/         # 后端依赖缓存
├── scripts/
│   ├── setup_dev_cache.sh  # 设置缓存脚本
│   ├── dev_start.sh         # 开发启动脚本
│   └── update_cache.sh      # 更新缓存脚本
├── docker-compose.yml        # 生产环境配置
├── docker-compose.dev.yml    # 开发环境配置
└── frontend/
    ├── frontend.Dockerfile      # 生产前端Dockerfile
    ├── frontend.Dockerfile.dev  # 开发前端Dockerfile
    └── .dockerignore            # 前端Docker忽略文件
```
