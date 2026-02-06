# 路由冲突分析报告

## 发现的重复路由

### 1. `main.py` 中的重复路由（已修复）

以下路由已在 `flight_endpoints.py` 中定义，但在 `main.py` 中也有定义，导致冲突：

- ❌ `GET /api/flights` (main.py:81) - **已删除**
- ❌ `GET /api/flights/statistics` (main.py:108) - **已删除**
- ❌ `POST /api/flights/batch-save` (main.py:148) - **已删除**

### 2. `docker_main.py` 中的重复路由（已修复）

以下路由已在对应的 endpoint 文件中定义，但在 `docker_main.py` 中也有定义：

- ❌ `POST /api/tasks` (docker_main.py:304) - **已删除**
- ❌ `GET /api/flights/statistics` (docker_main.py:110) - **已删除**
- ❌ `POST /api/flights/batch-save` (docker_main.py:140) - **已删除**
- ❌ `GET /api/tasks` (docker_main.py:238) - **已删除**
- ❌ `GET /api/tasks/statistics` (docker_main.py:259) - **已删除**

## 前端调用的路由

### 任务相关路由

| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/tasks` | `GET /api/tasks/` (task_endpoints.py) | ✅ 正常 |
| `POST /api/tasks/` | `POST /api/tasks/` (task_endpoints.py) | ✅ 正常 |
| `GET /api/tasks/stats` | `GET /api/tasks/stats` (task_endpoints.py) | ✅ 正常 |

### 航班相关路由

| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/flights/?...` | `GET /api/flights/` (flight_endpoints.py) | ✅ 正常 |
| `GET /api/flights/statistics` | `GET /api/flights/statistics` (flight_endpoints.py) | ✅ 正常 |

## 路由注册顺序

在 `docker_main.py` 中，路由注册顺序为：

```python
app.include_router(task_router, prefix="/api")      # /api/tasks/*
app.include_router(admin_router, prefix="/api")     # /api/admin/*
app.include_router(system_router, prefix="/api")    # /api/system/*
app.include_router(flight_router, prefix="/api")    # /api/flights/*
```

## 修复措施

1. ✅ 删除 `main.py` 中的重复路由定义
2. ✅ 删除 `docker_main.py` 中的重复路由定义
3. ✅ 确保 `main.py` 也注册 `flight_router`
4. ✅ 重新组织路由顺序，确保具体路径在参数路径之前

## 验证清单

- [x] 删除 `main.py` 中的 `/api/flights` 路由
- [x] 删除 `main.py` 中的 `/api/flights/statistics` 路由
- [x] 删除 `main.py` 中的 `/api/flights/batch-save` 路由
- [x] 删除 `docker_main.py` 中的 `/api/tasks` POST 路由
- [x] 删除 `docker_main.py` 中的 `/api/flights/statistics` 路由
- [x] 删除 `docker_main.py` 中的 `/api/flights/batch-save` 路由
- [x] 删除 `docker_main.py` 中的 `/api/tasks` GET 路由
- [x] 删除 `docker_main.py` 中的 `/api/tasks/statistics` 路由
- [x] 确保 `main.py` 注册 `flight_router`
- [x] 重新组织 `task_endpoints.py` 路由顺序
- [x] 重新组织 `flight_endpoints.py` 路由顺序
