# 批量任务创建和摘要生成指南

## 功能概述

系统现在支持：
1. **批量创建任务**：一次创建多个搜索任务
2. **任务调度执行**：支持按顺序执行（一个完成后执行下一个）或并行执行
3. **任务摘要生成**：生成包含任务名称、创建时间、启动时间、结束时间、抓取结果数等信息的摘要

## API 端点

### 1. 批量创建任务

**端点**: `POST /api/tasks/batch`

**请求体**:
```json
{
  "tasks": [
    {
      "task_name": "北京-上海-2026-01-27-12306-深圳航空",
      "task_type": "flight_scraper",
      "source": "12306",
      "config": {
        "fromCity": "北京",
        "toCity": "上海",
        "departDate": "2026-01-27"
      },
      "airline": "深圳航空"
    },
    {
      "task_name": "北京-广州-2026-01-28-12306-全部",
      "task_type": "flight_scraper",
      "source": "12306",
      "config": {
        "fromCity": "北京",
        "toCity": "广州",
        "departDate": "2026-01-28"
      },
      "airline": "全部"
    }
  ],
  "execute_immediately": true,
  "sequential": true
}
```

**参数说明**:
- `tasks`: 任务配置列表，每个任务包含：
  - `task_name`: 可选，任务名称（如果不提供会自动生成）
  - `task_type`: 任务类型，默认 `flight_scraper`
  - `source`: 数据源，默认 `12306`
  - `config`: 任务配置字典（包含 fromCity, toCity, departDate）
  - `airline`: 可选，指定航空公司
- `execute_immediately`: 是否立即执行，默认 `true`
- `sequential`: 是否按顺序执行，默认 `true`
  - `true`: 一个任务完成后执行下一个（顺序执行）
  - `false`: 所有任务同时启动（并行执行）

**响应**: 返回创建的任务记录列表

### 2. 获取单个任务摘要

**端点**: `GET /api/tasks/{task_id}/summary`

**响应示例**:
```json
{
  "task_id": 123,
  "task_name": "北京-上海-2026-01-27-12306-深圳航空",
  "created_at": "2026-01-27T10:00:00+08:00",
  "start_time": "2026-01-27T10:00:05+08:00",
  "end_time": "2026-01-27T10:15:30+08:00",
  "duration": 925,
  "duration_formatted": "15分钟25秒",
  "status": "completed",
  "success": true,
  "flights_count": 45,
  "error_message": null,
  "source": "12306",
  "airline": "深圳航空",
  "current_step": "完成"
}
```

### 3. 批量获取任务摘要

**端点**: `POST /api/tasks/batch/summary`

**请求体**:
```json
{
  "task_ids": [123, 124, 125]
}
```

**响应示例**:
```json
{
  "summaries": [
    {
      "task_id": 123,
      "task_name": "北京-上海-2026-01-27-12306-深圳航空",
      "created_at": "2026-01-27T10:00:00+08:00",
      "start_time": "2026-01-27T10:00:05+08:00",
      "end_time": "2026-01-27T10:15:30+08:00",
      "duration": 925,
      "duration_formatted": "15分钟25秒",
      "status": "completed",
      "success": true,
      "flights_count": 45
    }
  ],
  "statistics": {
    "total_tasks": 3,
    "successful_tasks": 2,
    "failed_tasks": 1,
    "running_tasks": 0,
    "success_rate": 66.67,
    "total_flights": 120,
    "avg_duration": 850.5,
    "total_duration": 2551.5,
    "total_duration_formatted": "42分钟31秒"
  }
}
```

### 4. 根据日期范围获取任务摘要

**端点**: `GET /api/tasks/summary/range?start_date=2026-01-27T00:00:00&end_date=2026-01-28T23:59:59&status=completed`

**查询参数**:
- `start_date`: 开始日期（ISO格式，可选）
- `end_date`: 结束日期（ISO格式，可选）
- `status`: 任务状态筛选（可选，如 `completed`, `running`, `failed`）

## 使用示例

### Python 示例

```python
import requests

# 批量创建任务（顺序执行）
response = requests.post('http://localhost:8000/api/tasks/batch', json={
    "tasks": [
        {
            "config": {
                "fromCity": "北京",
                "toCity": "上海",
                "departDate": "2026-01-27"
            },
            "airline": "深圳航空"
        },
        {
            "config": {
                "fromCity": "北京",
                "toCity": "广州",
                "departDate": "2026-01-28"
            },
            "airline": "全部"
        }
    ],
    "execute_immediately": True,
    "sequential": True
})

tasks = response.json()
task_ids = [task['id'] for task in tasks]

# 等待任务完成后获取摘要
import time
time.sleep(60)  # 等待任务执行

# 获取批量摘要
summary_response = requests.post(
    'http://localhost:8000/api/tasks/batch/summary',
    json={"task_ids": task_ids}
)
summary = summary_response.json()

print(f"总任务数: {summary['statistics']['total_tasks']}")
print(f"成功任务数: {summary['statistics']['successful_tasks']}")
print(f"总航班数: {summary['statistics']['total_flights']}")

for task_summary in summary['summaries']:
    print(f"{task_summary['task_name']}: {task_summary['flights_count']} 个航班")
```

### cURL 示例

```bash
# 批量创建任务
curl -X POST "http://localhost:8000/api/tasks/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "config": {
          "fromCity": "北京",
          "toCity": "上海",
          "departDate": "2026-01-27"
        },
        "airline": "深圳航空"
      }
    ],
    "execute_immediately": true,
    "sequential": true
  }'

# 获取任务摘要
curl "http://localhost:8000/api/tasks/123/summary"

# 批量获取摘要
curl -X POST "http://localhost:8000/api/tasks/batch/summary" \
  -H "Content-Type: application/json" \
  -d '{"task_ids": [123, 124, 125]}'
```

## 任务执行模式

### 顺序执行（Sequential）

- 一个任务完成后，自动开始执行下一个任务
- 适合需要避免资源冲突的场景
- 确保任务按顺序完成

### 并行执行（Parallel）

- 所有任务同时启动
- 适合任务之间相互独立的场景
- 可以更快完成所有任务

## 摘要信息说明

任务摘要包含以下信息：

- **task_id**: 任务ID
- **task_name**: 任务名称
- **created_at**: 创建时间
- **start_time**: 启动时间（任务开始执行的时间）
- **end_time**: 结束时间（任务完成的时间）
- **duration**: 执行时长（秒）
- **duration_formatted**: 格式化的执行时长（如 "15分钟25秒"）
- **status**: 任务状态（running, completed, failed）
- **success**: 是否成功
- **flights_count**: 抓取结果数（实时统计）
- **error_message**: 错误信息（如果有）
- **source**: 数据源
- **airline**: 指定航空公司
- **current_step**: 当前执行步骤

## 注意事项

1. 批量创建任务时，建议使用顺序执行模式，避免资源竞争
2. 任务摘要中的 `flights_count` 是实时统计的，反映当前数据库中的实际航班数量
3. 日期范围查询时，日期格式必须为 ISO 8601 格式
4. 任务执行是异步的，创建任务后需要等待一段时间才能获取完整的摘要信息
