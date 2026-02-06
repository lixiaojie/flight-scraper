# 502错误修复总结

## 🎯 问题确认

**问题**: 前端访问 `/api/tasks/` 和 `/api/flights/` 时返回 502 Bad Gateway 错误

**根本原因**: 后端服务启动失败，原因是Python语法错误

## 🔍 诊断过程

### 1. 服务状态检查
```bash
docker-compose ps
```
**结果**: `flight-scraper-web-1` 状态为 `Exited (1)` - 服务已退出

### 2. 查看退出日志
```bash
docker logs flight-scraper-web-1
```
**结果**: 发现语法错误
```
SyntaxError: name '_lock_acquired_time' is assigned to before global declaration
File "/app/services/task_scheduler.py", line 313
```

### 3. 定位问题
在 `task_scheduler.py` 的 `_run_single_task` 方法中：
- 第209行：只声明了 `global _task_execution_lock, _current_executing_task_id`
- 第216行：在 `with` 块内才声明 `global _lock_acquired_time`
- 第218行：在 `global` 声明之前就使用了 `_lock_acquired_time = time.time()`

**Python要求**: 所有 `global` 变量必须在函数开始处声明

## ✅ 修复方案

### 修复内容
1. **将 `global _lock_acquired_time` 移到函数开始处**（第209行）
2. **删除 `finally` 块中的重复 `global` 声明**（第313行）

### 修复后的代码
```python
def _run_single_task(self, task_id: int):
    """执行单个任务（同步执行，会等待任务完成）"""
    global _task_execution_lock, _current_executing_task_id, _lock_acquired_time  # ✅ 在函数开始处声明
    
    try:
        with _task_execution_lock:
            # ✅ 不再需要在这里声明 global
            _current_executing_task_id = task_id
            _lock_acquired_time = time.time()
            # ...
        finally:
            # ✅ 不再需要在这里声明 global
            _current_executing_task_id = None
            _lock_acquired_time = None
```

## 📋 验证步骤

### 步骤1: 检查语法
```bash
docker exec flight-scraper-web-1 python -m py_compile /app/services/task_scheduler.py
```
**预期**: 无错误输出

### 步骤2: 重启服务
```bash
docker-compose restart web
```

### 步骤3: 检查服务状态
```bash
docker-compose ps web
docker-compose logs --tail=50 web
```
**预期**: 
- 容器状态为 `Up`
- 日志中看到 "✅ 路由导入成功" 和 "✅ 路由注册完成"

### 步骤4: 测试API端点
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/tasks/
curl http://localhost:8000/api/flights/
```
**预期**: 返回正常JSON响应

### 步骤5: 测试前端访问
```bash
curl http://localhost:3002/api/tasks/
curl http://localhost:3002/api/flights/
```
**预期**: 返回正常JSON响应，不再出现502错误

## 📝 诊断计划更新

基于本次诊断，已更新诊断计划：

### 新增步骤0: 服务状态检查（最高优先级）
- 检查所有容器状态
- 检查是否有容器退出
- 如果服务退出，查看退出日志
- 检查Python语法错误

### 更新后的诊断流程
1. **步骤0**: 检查服务是否运行（最高优先级）
2. **步骤1**: 检查服务状态（仅在服务运行时）
3. **步骤2**: 检查路由导入状态
4. **步骤3**: 检查路由注册状态
5. **步骤4**: 检查Nginx代理状态

## 🎓 经验教训

1. **服务未启动是502错误的最常见原因**
   - 应该首先检查服务是否运行
   - 如果服务退出，立即查看日志

2. **Python语法错误会导致服务无法启动**
   - `global` 变量必须在函数开始处声明
   - 不能在代码块内声明 `global` 变量

3. **诊断计划需要包含服务状态检查**
   - 在检查路由、导入等之前，先确认服务是否运行

4. **Docker日志是诊断的关键**
   - `docker logs <container_name>` 可以快速定位问题
   - 退出码1通常表示启动失败

## 📊 修复状态

- ✅ 语法错误已修复
- ⏳ 等待重启服务验证
- ⏳ 等待测试API端点
- ⏳ 等待测试前端访问

## 🚀 下一步

1. 重启后端服务
2. 验证服务正常启动
3. 测试所有API端点
4. 确认前端可以正常访问
