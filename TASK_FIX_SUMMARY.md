# 任务创建和时区问题修复总结

## 问题1: 任务日志未创建

### 问题描述
前端通过 `/api/tasks/` 创建任务后，任务列表中有显示，但后台没有生成对应的 `task-{id}.log` 日志文件。

### 根本原因
前端调用的是 `task_endpoints.py` 中的 `/api/tasks/` 路由，该路由只是创建了任务记录，但没有启动后台抓取脚本。而任务日志是在 `docker_main.py` 的 `_run_scraper_and_update()` 函数中创建的。

### 解决方案
在 `task_endpoints.py` 的 `create_task_record` 函数中，添加了启动后台抓取脚本的逻辑：

1. 检查任务类型是否为 `flight_scraper` 且来源为 `12306`
2. 动态导入 `docker_main` 模块中的 `_run_scraper_and_update` 函数
3. 启动后台线程执行抓取脚本，这样会：
   - 创建任务日志文件 `task-{id}.log`
   - 执行航班抓取脚本
   - 更新任务状态和结果

### 代码修改
- `backend/api/endpoints/task_endpoints.py`: 添加后台脚本启动逻辑

## 问题2: 时区显示错误

### 问题描述
前端显示的任务开始时间为 11月1日13:25，但实际应该是 11月1日21:25（相差8小时）。

### 根本原因
- 容器内使用UTC时区（UTC+0）
- 用户在中国（UTC+8）
- `datetime.now()` 返回UTC时间，前端直接显示导致时间少8小时

### 解决方案
1. 添加 `pytz` 依赖包
2. 在 `TaskRecord` 模型中，使用 `pytz.timezone('Asia/Shanghai')` 获取当前上海时区时间
3. 在 `to_dict()` 方法中，将所有时间转换为Asia/Shanghai时区并格式化

### 代码修改
- `backend/requirements.txt`: 添加 `pytz==2024.1`
- `backend/models/task_record.py`: 
  - 修改 `start_time` 和 `created_at` 的默认值为Asia/Shanghai时区
  - 修改 `to_dict()` 中的时间格式化逻辑，确保转换为Asia/Shanghai时区
- `backend/services/task_service.py`: 
  - 更新任务结束时间时使用Asia/Shanghai时区
  - 修复时长计算逻辑

## 测试验证

### 任务日志创建
1. 前端创建新任务
2. 检查 `/app/results/task-{id}.log` 文件是否创建
3. 查看日志内容是否正确

### 时区显示
1. 创建新任务
2. 检查前端显示的开始时间是否为北京时间（UTC+8）
3. 验证时间显示正确性

## 注意事项

1. **时区存储**: 为了兼容SQLAlchemy的DateTime类型（不支持时区），我们在存储时将时区信息移除，但假设所有时间都是Asia/Shanghai时区。在返回给前端时再添加时区信息。

2. **日志文件路径**: 日志文件保存在 `/app/results/` 目录，该目录通过Docker volume挂载到主机的 `results/` 目录。

3. **后台线程**: 使用daemon线程执行抓取脚本，即使主进程退出，任务也会继续执行。
