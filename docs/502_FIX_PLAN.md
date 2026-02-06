# 502错误修复计划

## 📊 问题分析总结

基于之前的会话记录和代码检查，502错误的可能原因按优先级排序：

### 🔴 高优先级问题

#### 1. **后端服务启动失败**（最可能）
- **症状**: 容器运行但服务未启动，或启动后立即崩溃
- **可能原因**:
  - Python语法错误
  - 导入错误（ImportError）
  - 路由注册失败
  - 数据库连接失败
- **检查命令**:
  ```bash
  docker-compose logs --tail=100 web
  docker exec flight-scraper-web-1 ps aux | grep uvicorn
  curl -v http://localhost:8000/health
  ```

#### 2. **路由导入失败导致路由未注册**
- **症状**: 服务启动但 `HAS_ROUTERS=False`，所有 `/api/*` 请求失败
- **可能原因**:
  - `task_endpoints.py` 导入失败
  - `flight_endpoints.py` 导入失败
  - 依赖的服务类（`TaskScheduler`, `TaskSummaryService`）导入失败
  - 循环导入问题
- **检查命令**:
  ```bash
  docker-compose logs web | grep -i "路由\|router\|import\|HAS_ROUTERS"
  docker exec flight-scraper-web-1 python -c "from api.endpoints.task_endpoints import router"
  ```

### 🟡 中优先级问题

#### 3. **路由冲突（已部分修复，需确认）**
- **状态**: `docker_main.py` 已清理，`main.py` 已注释，但需确认无遗漏
- **检查命令**:
  ```bash
  grep -n "@app\.\(get\|post\|put\|delete\)" backend/docker_main.py
  grep -n "@app\.\(get\|post\|put\|delete\)" backend/main.py
  ```

#### 4. **数据库连接问题**
- **症状**: 应用启动时数据库操作失败
- **检查命令**:
  ```bash
  ls -la data/flight_scraper.db
  docker exec flight-scraper-web-1 python -c "from core.database import get_db; next(get_db())"
  ```

### 🟢 低优先级问题

#### 5. **Nginx代理配置问题**
- **症状**: nginx无法连接到后端
- **检查命令**:
  ```bash
  docker exec flight-scraper-frontend-1 wget -qO- http://web:8000/health
  docker-compose logs frontend | grep -i error
  ```

## 🎯 解决计划（按执行顺序）

### 阶段0: 服务状态检查（最高优先级，1分钟）

#### 步骤0.1: 检查服务是否运行
```bash
# 1. 检查所有容器状态
docker-compose ps

# 2. 检查是否有容器退出
docker ps -a | grep Exited

# 3. 如果web服务退出，查看退出日志
docker logs flight-scraper-web-1 2>&1 | tail -100
```

**预期结果**:
- 所有服务状态应为 `Up`
- 没有 `Exited` 状态的容器

**如果服务未运行**:
- 查看日志找出原因（语法错误、导入错误等）
- 根据错误信息修复问题
- 修复后重启服务

#### 步骤0.2: 检查语法错误（如果服务未启动）
```bash
# 检查Python语法
docker exec flight-scraper-web-1 python -m py_compile /app/docker_main.py 2>&1
docker exec flight-scraper-web-1 python -m py_compile /app/services/task_scheduler.py 2>&1
docker exec flight-scraper-web-1 python -m py_compile /app/api/endpoints/task_endpoints.py 2>&1
```

**如果发现语法错误**:
- 修复语法错误
- 重新检查语法
- 重启服务

### 阶段1: 立即诊断（5分钟）

#### 步骤1.1: 检查后端服务状态（仅在服务运行时）
```bash
# 1. 检查容器是否运行
docker-compose ps web

# 2. 查看最近100行日志
docker-compose logs --tail=100 web

# 3. 检查服务是否响应
curl -v http://localhost:8000/health
curl -v http://localhost:8000/

# 4. 检查进程
docker exec flight-scraper-web-1 ps aux | grep -E "uvicorn|python"
```

**预期结果**:
- 容器状态应为 `Up`
- 日志中应看到 "✅ 路由导入成功" 和 "✅ 路由注册完成"
- `/health` 端点应返回 `{"status": "healthy", ...}`

**如果失败**:
- 记录错误信息，进入步骤1.2

#### 步骤1.2: 检查路由导入状态
```bash
# 1. 查看路由导入日志
docker-compose logs web | grep -E "路由|router|HAS_ROUTERS|ImportError|ModuleNotFoundError"

# 2. 手动测试路由导入
docker exec flight-scraper-web-1 python <<'EOF'
import sys
sys.path.insert(0, '/app')

print("=" * 50)
print("测试路由导入")
print("=" * 50)

routers = [
    ('task_endpoints', 'task_router'),
    ('flight_endpoints', 'flight_router'),
    ('admin_endpoints', 'admin_router'),
    ('system_endpoints', 'system_router'),
]

for module_name, router_name in routers:
    try:
        module = __import__(f'api.endpoints.{module_name}', fromlist=[router_name])
        router = getattr(module, router_name)
        print(f"✅ {module_name}.{router_name} 导入成功")
    except Exception as e:
        print(f"❌ {module_name}.{router_name} 导入失败: {e}")
        import traceback
        traceback.print_exc()

print("=" * 50)
print("测试服务类导入")
print("=" * 50)

services = [
    ('services.task_scheduler', 'TaskScheduler'),
    ('services.task_summary', 'TaskSummaryService'),
]

for module_name, class_name in services:
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"✅ {module_name}.{class_name} 导入成功")
    except Exception as e:
        print(f"⚠️ {module_name}.{class_name} 导入失败: {e}")

EOF
```

**预期结果**:
- 所有路由应导入成功
- 服务类导入失败是允许的（有 `HAS_SCHEDULER` 保护）

**如果失败**:
- 记录具体导入错误，进入阶段2修复

#### 步骤1.3: 检查路由注册状态
```bash
# 检查FastAPI应用的路由列表
docker exec flight-scraper-web-1 python <<'EOF'
import sys
sys.path.insert(0, '/app')
from docker_main import app

print("=" * 50)
print("已注册的路由列表")
print("=" * 50)

routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        routes.append((methods, route.path))

# 按路径排序
routes.sort(key=lambda x: x[1])

for methods, path in routes:
    print(f"{methods:15} {path}")

print("=" * 50)
print(f"总计: {len(routes)} 个路由")
print("=" * 50)

# 检查关键路由
key_routes = [
    '/api/tasks/',
    '/api/flights/',
    '/api/tasks/stats',
    '/api/flights/statistics',
]

print("\n关键路由检查:")
for key_route in key_routes:
    found = any(path == key_route or path.startswith(key_route) for _, path in routes)
    status = "✅" if found else "❌"
    print(f"{status} {key_route}")
EOF
```

**预期结果**:
- 应看到所有 `/api/tasks/*` 和 `/api/flights/*` 路由
- 关键路由都应存在

**如果失败**:
- 路由未注册，进入阶段2修复

#### 步骤1.4: 检查Nginx代理
```bash
# 1. 检查nginx配置
docker exec flight-scraper-frontend-1 nginx -t

# 2. 检查nginx错误日志
docker-compose logs frontend | grep -i error | tail -20

# 3. 测试nginx到后端的连接
docker exec flight-scraper-frontend-1 wget -qO- http://web:8000/health

# 4. 测试前端API代理
curl -v http://localhost:3002/api/tasks/
curl -v http://localhost:3002/api/flights/
```

**预期结果**:
- nginx配置语法正确
- nginx可以连接到后端
- 前端API代理正常工作

**如果失败**:
- 记录错误信息，进入阶段2修复

### 阶段2: 修复问题（根据诊断结果）

#### 修复2.1: 修复路由导入失败

**如果 `task_endpoints.py` 导入失败**:
1. 检查 `task_endpoints.py` 中的导入语句
2. 检查依赖的服务类是否可以导入
3. 修复循环导入问题
4. 确保 `HAS_SCHEDULER` 保护正确

**如果 `flight_endpoints.py` 导入失败**:
1. 检查 `flight_endpoints.py` 中的导入语句
2. 检查依赖的模型和schema是否可以导入

#### 修复2.2: 修复路由冲突

**检查并删除所有重复路由**:
```bash
# 检查 docker_main.py
grep -n "@app\.\(get\|post\|put\|delete\|patch\)" backend/docker_main.py

# 检查 main.py
grep -n "@app\.\(get\|post\|put\|delete\|patch\)" backend/main.py
```

**如果发现重复路由**:
- 删除或注释掉重复的路由定义
- 确保所有路由都通过 router 注册

#### 修复2.3: 修复数据库连接问题

**如果数据库连接失败**:
1. 检查数据库文件是否存在: `ls -la data/flight_scraper.db`
2. 检查数据库文件权限
3. 检查数据库初始化脚本
4. 添加数据库连接重试机制

#### 修复2.4: 修复Nginx代理问题

**如果nginx无法连接到后端**:
1. 检查Docker网络配置
2. 检查nginx配置中的后端地址（应为 `http://web:8000`）
3. 检查后端服务是否在8000端口监听
4. 增加nginx代理超时时间

### 阶段3: 验证修复（修复后）

#### 步骤3.1: 重启服务
```bash
# 重启后端服务
docker-compose restart web

# 等待服务启动
sleep 5

# 重启前端服务
docker-compose restart frontend

# 等待服务启动
sleep 3
```

#### 步骤3.2: 验证后端服务
```bash
# 1. 检查服务状态
docker-compose ps

# 2. 测试健康检查
curl http://localhost:8000/health

# 3. 测试API端点
curl http://localhost:8000/api/tasks/
curl http://localhost:8000/api/flights/
curl http://localhost:8000/api/tasks/stats
curl http://localhost:8000/api/flights/statistics
```

#### 步骤3.3: 验证前端访问
```bash
# 1. 测试前端页面
curl http://localhost:3002/

# 2. 测试前端API代理
curl http://localhost:3002/api/tasks/
curl http://localhost:3002/api/flights/
```

#### 步骤3.4: 监控日志
```bash
# 实时监控后端日志
docker-compose logs -f web

# 实时监控前端日志
docker-compose logs -f frontend
```

## 📋 执行检查清单

### 阶段0: 服务状态检查（最高优先级）
- [ ] 检查所有容器状态
- [ ] 检查是否有容器退出
- [ ] 如果服务退出，查看退出日志
- [ ] 检查Python语法错误（如果服务未启动）
- [ ] 修复发现的问题
- [ ] 重启服务并确认运行

### 诊断阶段（仅在服务运行时）
- [ ] 检查后端服务状态
- [ ] 检查路由导入状态
- [ ] 检查路由注册状态
- [ ] 检查Nginx代理状态
- [ ] 记录所有错误信息

### 修复阶段（根据诊断结果）
- [ ] 修复路由导入失败
- [ ] 修复路由冲突
- [ ] 修复数据库连接问题
- [ ] 修复Nginx代理问题

### 验证阶段
- [ ] 重启服务
- [ ] 验证后端服务
- [ ] 验证前端访问
- [ ] 监控日志确认无错误

## 🚨 紧急修复（如果问题持续）

如果按照上述步骤仍无法解决，执行以下紧急修复：

1. **完全重建容器**
   ```bash
   docker-compose down
   docker-compose build --no-cache web
   docker-compose up -d
   ```

2. **检查并修复所有导入错误**
   ```bash
   docker exec flight-scraper-web-1 python -m py_compile docker_main.py
   docker exec flight-scraper-web-1 python -c "import docker_main"
   ```

3. **简化路由注册**（临时方案）
   - 如果路由导入持续失败，可以临时在 `docker_main.py` 中直接定义关键路由

4. **检查系统资源**
   ```bash
   docker stats
   df -h
   free -h
   ```

## 📝 问题报告模板

如果问题仍然存在，请提供以下信息：

```
1. 后端服务状态:
   - 容器状态: [Up/Down/Exited]
   - 日志最后50行: [粘贴日志]
   - /health 端点响应: [粘贴响应]

2. 路由导入状态:
   - 路由导入测试结果: [粘贴结果]
   - 是否有导入错误: [是/否]
   - 错误信息: [粘贴错误]

3. 路由注册状态:
   - 已注册路由数量: [数字]
   - 关键路由是否存在: [是/否]
   - 路由列表: [粘贴列表]

4. Nginx代理状态:
   - nginx配置检查: [通过/失败]
   - nginx到后端连接: [成功/失败]
   - 前端API代理测试: [成功/失败]

5. 其他信息:
   - Docker版本: [版本号]
   - 系统信息: [操作系统版本]
   - 最近修改: [描述最近的代码修改]
```
