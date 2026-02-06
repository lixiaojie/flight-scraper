# 前端API调用修复

## 问题描述

前端访问任务列表时出现错误：
```
GET http://localhost/api/tasks/ net::ERR_CONNECTION_REFUSED
```

## 问题分析

1. **错误URL**: `http://localhost/api/tasks/` - 缺少端口号
2. **正确URL**: `http://localhost:3002/api/tasks/` - 应该包含端口号
3. **nginx代理测试**: 通过 `curl http://localhost:3002/api/tasks/` 测试正常，返回200 OK

## 根本原因

`frontend/src/lib/api.ts` 中的 `getApiBase()` 函数在浏览器环境中返回空字符串 `''`，使用相对路径。当浏览器解析相对路径 `/api/tasks/` 时，如果当前页面的URL是 `http://localhost/`（没有端口），就会生成 `http://localhost/api/tasks/`（缺少端口）。

## 修复方案

修改 `getApiBase()` 函数，在浏览器环境中使用 `window.location.origin`，确保包含协议、主机和端口：

```typescript
export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    // 使用当前页面的origin，确保包含端口号
    // 例如：http://localhost:3002
    return window.location.origin;
  }
  // ...
}
```

## 修复内容

1. ✅ 修改 `frontend/src/lib/api.ts` - 使用 `window.location.origin` 而不是空字符串
2. ✅ 修改 `frontend/src/pages/Dashboard.tsx` - 使用 `apiFetch` 而不是直接 `fetch`

## 验证步骤

1. 重新构建前端
   ```bash
   docker-compose build frontend
   docker-compose up -d frontend
   ```

2. 测试前端访问
   - 访问 `http://localhost:3002/task-records`
   - 检查浏览器控制台，应该不再出现 `ERR_CONNECTION_REFUSED` 错误
   - 任务列表应该正常显示

3. 检查网络请求
   - 打开浏览器开发者工具 -> Network
   - 查看 `/api/tasks/` 请求
   - URL应该是 `http://localhost:3002/api/tasks/`（包含端口）

## 注意事项

- 确保用户访问的是 `http://localhost:3002/` 而不是 `http://localhost/`
- 如果用户访问的是 `http://localhost/`，仍然会出现问题，因为端口80上没有服务
