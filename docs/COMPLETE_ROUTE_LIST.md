# 完整路由清单

## 路由定义位置

### 1. task_endpoints.py (prefix="/tasks")

| 序号 | 方法 | 路径 | 完整路径 | 状态 |
|------|------|------|----------|------|
| 1 | GET | `/summary/range` | `/api/tasks/summary/range` | ✅ |
| 2 | POST | `/batch/summary` | `/api/tasks/batch/summary` | ✅ |
| 3 | POST | `/batch` | `/api/tasks/batch` | ✅ |
| 4 | GET | `/stats` | `/api/tasks/stats` | ✅ |
| 5 | DELETE | `/cleanup` | `/api/tasks/cleanup` | ✅ |
| 6 | GET | `/` | `/api/tasks/` | ✅ |
| 7 | POST | `/` | `/api/tasks/` | ✅ |
| 8 | GET | `/{task_id:int}/summary` | `/api/tasks/{task_id}/summary` | ✅ |
| 9 | PUT | `/{task_id}/result` | `/api/tasks/{task_id}/result` | ✅ |
| 10 | PUT | `/{task_id}/notes` | `/api/tasks/{task_id}/notes` | ✅ |
| 11 | GET | `/{task_id:int}` | `/api/tasks/{task_id}` | ✅ |

### 2. flight_endpoints.py (prefix="/flights")

| 序号 | 方法 | 路径 | 完整路径 | 状态 |
|------|------|------|----------|------|
| 1 | GET | `/by-time-range` | `/api/flights/by-time-range` | ✅ |
| 2 | GET | `/by-date` | `/api/flights/by-date` | ✅ |
| 3 | GET | `/statistics` | `/api/flights/statistics` | ✅ |
| 4 | POST | `/batch-save` | `/api/flights/batch-save` | ✅ |
| 5 | DELETE | `/cleanup` | `/api/flights/cleanup` | ✅ |
| 6 | GET | `/` | `/api/flights/` | ✅ |

### 3. admin_endpoints.py (prefix="/admin")

| 序号 | 方法 | 路径 | 完整路径 | 状态 |
|------|------|------|----------|------|
| 1 | POST | `/login` | `/api/admin/login` | ✅ |
| 2 | POST | `/create` | `/api/admin/create` | ✅ |
| 3 | GET | `/me` | `/api/admin/me` | ✅ |
| 4 | PUT | `/password` | `/api/admin/password` | ✅ |

### 4. system_endpoints.py (prefix="/system")

| 序号 | 方法 | 路径 | 完整路径 | 状态 |
|------|------|------|----------|------|
| 1 | GET | `/status` | `/api/system/status` | ✅ |
| 2 | POST | `/start` | `/api/system/start` | ✅ |
| 3 | POST | `/stop` | `/api/system/stop` | ✅ |
| 4 | POST | `/scraper/run` | `/api/system/scraper/run` | ✅ |
| 5 | GET | `/logs` | `/api/system/logs` | ✅ |

### 5. docker_main.py (直接定义在 app 上)

| 序号 | 方法 | 路径 | 完整路径 | 状态 | 说明 |
|------|------|------|----------|------|------|
| 1 | GET | `/` | `/` | ✅ | 根路径 |
| 2 | GET | `/health` | `/health` | ✅ | 健康检查 |
| 3 | POST | `/api/admin/login` | `/api/admin/login` | ⚠️ | 与 admin_endpoints 重复 |
| 4 | POST | `/api/v1/auth/login` | `/api/v1/auth/login` | ✅ | 兼容登录接口 |
| 5 | POST | `/api/v1/auth/login-debug` | `/api/v1/auth/login-debug` | ✅ | 调试接口 |
| 6 | POST | `/api/v1/auth/login-flexible` | `/api/v1/auth/login-flexible` | ✅ | 灵活登录接口 |

## 发现的重复路由（已修复）

### docker_main.py 中的重复路由

1. ❌ `POST /api/tasks` - **已删除**（与 `task_endpoints.py` 中的 `POST /api/tasks/` 冲突）
2. ❌ `GET /api/flights/statistics` - **已删除**（与 `flight_endpoints.py` 中的路由冲突）
3. ❌ `POST /api/flights/batch-save` - **已删除**（与 `flight_endpoints.py` 中的路由冲突）
4. ❌ `GET /api/tasks` - **已删除**（与 `task_endpoints.py` 中的 `GET /api/tasks/` 冲突）
5. ❌ `GET /api/tasks/statistics` - **已删除**（与 `task_endpoints.py` 中的 `GET /api/tasks/stats` 冲突）
6. ❌ `PATCH /api/tasks/{task_id}/status` - **已删除**（可能与 task_endpoints 冲突）
7. ❌ `GET /api/system/status` - **已删除**（与 `system_endpoints.py` 中的路由冲突）

### main.py 中的重复路由

1. ❌ `GET /api/flights` - **已删除**（与 `flight_endpoints.py` 中的路由冲突）
2. ❌ `GET /api/flights/statistics` - **已删除**（与 `flight_endpoints.py` 中的路由冲突）
3. ❌ `POST /api/flights/batch-save` - **已删除**（与 `flight_endpoints.py` 中的路由冲突）

## 前端调用的路由

### 任务列表页 (TaskRecords.tsx)

- `GET /api/tasks` - 获取任务列表 ✅
- `GET /api/tasks/stats` - 获取任务统计 ✅
- `POST /api/tasks/` - 创建任务 ✅

### 航班结果页 (FlightResults.tsx)

- `GET /api/flights/?...` - 获取航班列表 ✅
- `GET /api/flights/statistics` - 获取航班统计 ✅

## 路由冲突分析

### 潜在冲突点

1. **`POST /api/admin/login`**
   - `docker_main.py:351` - 直接定义
   - `admin_endpoints.py:63` - 通过 router 定义
   - **状态**: ⚠️ 可能冲突，但 `docker_main.py` 中的路由会优先匹配（因为直接定义在 app 上）

2. **路径参数类型不一致**
   - `GET /api/tasks/{task_id:int}` - 使用类型约束
   - `PUT /api/tasks/{task_id}/result` - 不使用类型约束
   - **状态**: ✅ 不冲突，FastAPI 会根据路径长度匹配

## 修复建议

1. ✅ 删除 `docker_main.py` 中的 `POST /api/admin/login` 路由（如果 `admin_endpoints.py` 中已有）
2. ✅ 确保所有路由都通过 router 注册，避免直接定义在 app 上
3. ✅ 统一路径参数的类型约束（都使用 `{task_id:int}` 或都不使用）
