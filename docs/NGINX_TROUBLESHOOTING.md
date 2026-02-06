# Nginx 前端访问问题排查指南

## ✅ 问题已解决

**根本原因**: 端口冲突 - 端口3000和3001都被其他进程占用

**解决方案**: 修改 `docker-compose.yml` 将前端端口映射改为 `3002:3000`

**当前访问地址**: `http://localhost:3002`

## 原始问题现象

浏览器访问 `http://localhost:3000` 时出现错误：
```
Not allowed to load local resource: chrome-error://chromewebdata/#buttons
ERR_EMPTY_RESPONSE
```

使用curl测试时：
```
curl: (56) Recv failure: Connection reset by peer
```

## 当前状态

### ✅ 正常工作的部分

1. **容器内部访问**: 完全正常
   ```bash
   docker exec flight-scraper-frontend-1 wget -qO- http://127.0.0.1:3000
   # 返回正常的HTML内容
   ```

2. **Nginx配置**: 语法正确，配置验证通过
   ```bash
   docker exec flight-scraper-frontend-1 nginx -t
   # nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
   ```

3. **容器运行状态**: 正常运行
   - Nginx master和worker进程都在运行
   - 端口3000正常监听（0.0.0.0:3000）
   - 静态文件存在且正确

4. **API代理**: 容器内部可以正常访问后端
   ```bash
   docker exec flight-scraper-frontend-1 wget -qO- http://web:8000/health
   # 返回正常的JSON响应
   ```

### ❌ 问题部分

1. **主机访问**: 连接建立后立即被重置
   ```bash
   curl http://localhost:3000
   # curl: (56) Recv failure: Connection reset by peer
   ```

## 问题原因总结

### ✅ 已确认: 端口冲突（已解决）

端口3000被Cursor编辑器占用，导致无法绑定。

**解决方案**:
```bash
# 检查端口占用
lsof -i :3000
lsof -i :3001

# 修改docker-compose.yml中的端口映射
ports:
  - "3002:3000"  # 使用空闲端口

# 重启服务
docker-compose up -d frontend

# 访问新端口
http://localhost:3002
```

## 其他可能的原因（已排除）

### 1. Docker Desktop 网络问题

macOS Docker Desktop的端口转发可能在IPv6/IPv4处理上有问题。

**解决方案**:
```bash
# 方法1: 重启Docker Desktop
# 在Docker Desktop中：Settings -> Reset to factory defaults (谨慎操作)

# 方法2: 重置Docker网络
docker network prune -f
docker-compose down
docker-compose up -d
```

### 2. 浏览器缓存问题

浏览器可能缓存了错误的响应。

**解决方案**:
- 清除浏览器缓存
- 使用无痕模式访问
- 或者访问: `http://127.0.0.1:3000` (不使用localhost)

### 3. 防火墙/安全软件

macOS防火墙或安全软件可能阻止连接。

**解决方案**:
- 检查系统偏好设置 -> 安全性与隐私 -> 防火墙
- 暂时禁用防火墙测试

## 临时解决方案

### 方案1: 使用容器IP直接访问

```bash
# 获取容器IP
CONTAINER_IP=$(docker inspect flight-scraper-frontend-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

# 在浏览器访问: http://<容器IP>:3000
echo "访问地址: http://$CONTAINER_IP:3000"
```

### 方案2: 使用端口转发

```bash
# 使用socat进行端口转发
brew install socat
socat TCP-LISTEN:3001,fork TCP:172.18.0.4:3000

# 然后访问 http://localhost:3001
```

### 方案3: 修改Docker端口映射

修改 `docker-compose.yml`:
```yaml
ports:
  - "127.0.0.1:3000:3000"  # 只绑定IPv4
```

## 验证步骤

1. **检查容器状态**:
   ```bash
   docker-compose ps frontend
   ```

2. **检查端口监听**:
   ```bash
   docker exec flight-scraper-frontend-1 netstat -tuln | grep 3000
   ```

3. **测试容器内部访问**:
   ```bash
   docker exec flight-scraper-frontend-1 wget -qO- http://127.0.0.1:3000
   ```

4. **测试主机访问**:
   ```bash
   curl -4 -v http://127.0.0.1:3000
   ```

## 当前配置摘要

- **Nginx监听**: `0.0.0.0:3000` (IPv4)
- **端口映射**: `0.0.0.0:3000->3000/tcp`
- **容器IP**: `172.18.0.4`
- **API代理**: `/api/` -> `http://web:8000/api/`

## 建议

由于容器内部访问完全正常，问题很可能是macOS Docker Desktop的网络层问题。建议：

1. 重启Docker Desktop
2. 检查Docker Desktop的网络设置
3. 如果问题持续，考虑使用Docker Desktop的虚拟机IP访问
