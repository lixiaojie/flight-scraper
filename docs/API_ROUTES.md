# API 路由清单

本文档列出了所有 API 路由及其逻辑关系。

## FastAPI 路由匹配规则

1. **具体路径必须在参数路径之前**
2. **更长的路径必须在更短的路径之前**
3. **相同路径但不同 HTTP 方法的路由可以共存**

## 路由清单

### 1. 任务管理路由 (`/api/tasks`)

#### 具体路径路由（按路径长度排序）

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| GET | `/api/tasks/summary/range` | 根据日期范围获取任务摘要 | 1 (最长) |
| POST | `/api/tasks/batch/summary` | 批量获取任务摘要 | 2 |
| POST | `/api/tasks/batch` | 批量创建任务 | 3 |
| GET | `/api/tasks/stats` | 获取任务统计信息 | 4 |
| DELETE | `/api/tasks/cleanup` | 清理旧任务记录 | 5 |

#### 根路径路由

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| GET | `/api/tasks/` | 获取任务记录列表 | 6 |
| POST | `/api/tasks/` | 创建任务记录 | 6 |

#### 参数路径路由（按路径长度排序）

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| GET | `/api/tasks/{task_id:int}/summary` | 获取任务摘要 | 7 (最长参数路径) |
| PUT | `/api/tasks/{task_id}/result` | 更新任务结果 | 8 |
| PUT | `/api/tasks/{task_id}/notes` | 更新任务备注 | 8 |
| GET | `/api/tasks/{task_id:int}` | 根据ID获取任务记录 | 9 (最短参数路径) |

### 2. 航班管理路由 (`/api/flights`)

#### 具体路径路由（按路径长度排序）

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| GET | `/api/flights/by-time-range` | 根据时间范围查询航班 | 1 (最长) |
| GET | `/api/flights/by-date` | 根据日期查询航班 | 2 |
| GET | `/api/flights/statistics` | 获取航班统计信息 | 3 |
| POST | `/api/flights/batch-save` | 批量保存航班数据 | 4 |
| DELETE | `/api/flights/cleanup` | 清理旧航班数据 | 5 |

#### 根路径路由

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| GET | `/api/flights/` | 获取航班列表 | 6 |

### 3. 管理员路由 (`/api/admin`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/login` | 管理员登录 |
| POST | `/api/admin/create` | 创建管理员账号 |
| GET | `/api/admin/me` | 获取当前管理员信息 |
| PUT | `/api/admin/password` | 修改密码 |

### 4. 系统控制路由 (`/api/system`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/status` | 获取系统状态 |
| POST | `/api/system/start` | 启动系统服务 |
| POST | `/api/system/stop` | 停止系统服务 |
| POST | `/api/system/scraper/run` | 运行抓取任务 |
| GET | `/api/system/logs` | 获取系统日志 |

## 路由冲突分析

### 潜在冲突点

1. **`/{task_id:int}` vs `/{task_id}`**
   - `GET /api/tasks/{task_id:int}` - 使用类型约束
   - `PUT /api/tasks/{task_id}/result` - 不使用类型约束
   - **解决方案**: FastAPI 会根据路径长度和具体程度匹配，`/{task_id}/result` 更具体，会优先匹配

2. **`/summary/range` vs `/{task_id:int}/summary`**
   - `/summary/range` 是具体路径
   - `/{task_id:int}/summary` 是参数路径
   - **解决方案**: 具体路径 `/summary/range` 必须在参数路径之前

## 路由顺序验证

### 任务路由顺序（正确）

```
1. GET  /summary/range          (具体路径，最长)
2. POST /batch/summary           (具体路径)
3. POST /batch                   (具体路径)
4. GET  /stats                   (具体路径)
5. DELETE /cleanup               (具体路径)
6. GET  /                        (根路径)
7. POST /                        (根路径)
8. GET  /{task_id:int}/summary   (参数路径，最长)
9. PUT  /{task_id}/result        (参数路径)
10. PUT /{task_id}/notes         (参数路径)
11. GET /{task_id:int}           (参数路径，最短)
```

### 航班路由顺序（正确）

```
1. GET  /by-time-range          (具体路径，最长)
2. GET  /by-date                (具体路径)
3. GET  /statistics             (具体路径)
4. POST /batch-save             (具体路径)
5. DELETE /cleanup              (具体路径)
6. GET  /                       (根路径)
```

## 注意事项

1. **路由顺序很重要**: FastAPI 按照路由定义的顺序进行匹配，第一个匹配的路由会被使用
2. **参数路径必须最后**: 所有包含路径参数的路由（如 `/{task_id:int}`）必须在所有具体路径之后
3. **更长的路径优先**: 如果两个路径都是参数路径，更长的路径（如 `/{task_id:int}/summary`）必须在更短的路径（如 `/{task_id:int}`）之前
