# 航班抓取系统 - Docker 容器状态报告

**生成时间**: 2025-12-14

## 📊 总体状态

✅ **所有服务正常运行**

所有三个核心服务都在运行，健康检查通过，已持续运行 2 天。

---

## 🐳 Docker 容器详细状态

### 1. 后端 API 服务 (flight-scraper-web-1)

- **状态**: ✅ Up 2 days (healthy)
- **镜像**: flight-scraper-web
- **端口映射**: `0.0.0.0:8000->8000/tcp`
- **健康检查**: ✅ healthy
- **资源使用**:
  - CPU: 0.24%
  - 内存: 61.33 MiB / 7.653 GiB
  - 网络 I/O: 3.62kB / 1.56kB
- **创建时间**: 2025-12-12 16:16:15
- **服务端点**:
  - 根路径: http://localhost:8000/ ✅
  - 健康检查: http://localhost:8000/health ✅
  - API 文档: http://localhost:8000/docs
  - 航班统计: http://localhost:8000/api/flights/statistics ✅

**最近日志**: 健康检查请求正常，服务响应正常

---

### 2. 前端服务 (flight-scraper-frontend-1)

- **状态**: ✅ Up 2 days
- **镜像**: flight-scraper-frontend
- **端口映射**: `0.0.0.0:3002->3000/tcp`
- **资源使用**:
  - CPU: 0.00%
  - 内存: 96.97 MiB / 7.653 GiB
  - 网络 I/O: 3.18kB / 1.41kB
- **创建时间**: 2025-12-12 16:16:15
- **服务端点**: http://localhost:3002 ✅

**最近日志**: Nginx 配置正常，服务正常响应

---

### 3. Appium 服务 (flight-scraper-appium-1)

- **状态**: ✅ Up 2 days (healthy)
- **镜像**: flight-scraper-appium
- **端口映射**: `0.0.0.0:4723->4723/tcp`
- **健康检查**: ✅ healthy
- **资源使用**:
  - CPU: 0.00%
  - 内存: 2.75 MiB / 7.653 GiB
  - 网络 I/O: 2.33kB / 1.31kB
- **创建时间**: 2025-12-12 16:16:15
- **服务端点**: http://localhost:4723/status ✅
- **版本**: Appium 3.0.2

**最近日志**: 状态检查请求正常，服务就绪

---

## 📈 服务功能测试结果

### API 端点测试

1. **根路径** ✅
   ```json
   {"message":"航班信息API服务正在运行","version":"1.0.0"}
   ```

2. **健康检查** ✅
   ```json
   {"status":"healthy","service":"flight-scraper-api"}
   ```

3. **航班统计** ✅
   ```json
   {
     "total_flights": 88,
     "min_price": 290.0,
     "max_price": 2500.0,
     "avg_price": 541.89
   }
   ```

4. **航班列表** ✅
   - 成功返回航班数据
   - 包含完整的航班信息（航空公司、航班号、时间、价格等）

### 前端服务测试

- ✅ HTML 页面正常加载
- ✅ 静态资源正常服务
- ✅ 应用标题: "航班信息抓取系统"

### Appium 服务测试

- ✅ 服务就绪，可接受新连接
- ✅ 版本: 3.0.2
- ✅ 健康检查通过

---

## 💾 数据库状态

- **数据库文件**: `/Users/admin/Downloads/flight-scraper/backend/flight_scraper.db`
- **文件大小**: 151 KB
- **数据统计**:
  - 航班记录: **88 条**
  - 任务记录: **56 条**
- **表结构**:
  - `flight_results` - 航班结果表
  - `task_records` - 任务记录表
  - `admins` - 管理员表

---

## 🌐 网络配置

- **Docker 网络**: `flight-scraper_app-network` (bridge)
- **网络 ID**: a4c6f14c5690
- **所有容器在同一网络中，可以互相通信**

---

## 📊 资源使用汇总

| 容器 | CPU | 内存 | 状态 |
|------|-----|------|------|
| web | 0.24% | 61.33 MiB | ✅ healthy |
| frontend | 0.00% | 96.97 MiB | ✅ running |
| appium | 0.00% | 2.75 MiB | ✅ healthy |
| **总计** | **0.24%** | **161.05 MiB** | **✅ 全部正常** |

**系统资源充足，所有服务运行稳定**

---

## 🔗 服务访问地址

| 服务 | 地址 | 状态 |
|------|------|------|
| 前端应用 | http://localhost:3002 | ✅ |
| 后端 API | http://localhost:8000 | ✅ |
| API 文档 | http://localhost:8000/docs | ✅ |
| Appium | http://localhost:4723 | ✅ |
| Appium 状态 | http://localhost:4723/status | ✅ |

---

## ✅ 结论

**系统运行状态: 优秀**

- ✅ 所有 Docker 容器正常运行
- ✅ 所有健康检查通过
- ✅ 所有服务端点可访问
- ✅ API 功能正常
- ✅ 数据库连接正常
- ✅ 资源使用合理
- ✅ 服务已稳定运行 2 天

**建议**: 系统运行良好，无需采取任何行动。可以继续正常使用。

---

## 📝 管理命令参考

```bash
# 查看容器状态
docker-compose ps
# 或
docker ps

# 查看日志
docker-compose logs -f [service_name]
# 或
docker logs [container_name] -f

# 重启服务
docker-compose restart [service_name]

# 停止服务
docker-compose down

# 启动服务
docker-compose up -d
```
