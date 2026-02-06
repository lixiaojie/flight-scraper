# Appium Inspector 连接问题修复指南

## 🚨 问题

使用 Appium Inspector 连接时出现错误：
```
Could not connect to Appium server URL 'http://127.0.0.1:4723'. 
Please check if the server is running and the URL is correct.
If you are using the Inspector's browser version, ensure the server has been started with '--allow-cors'.
```

## ✅ 解决方案

### 方案1：使用浏览器版 Appium Inspector（推荐）

Appium 3.x 已经内置了浏览器版的 Inspector，可以直接使用：

1. **访问浏览器版 Inspector**：
   - 打开浏览器，访问：`http://localhost:4723/inspector`
   - 或者访问：`http://127.0.0.1:4723/inspector`

2. **配置 Desired Capabilities**：
   - 在浏览器中粘贴以下 JSON 配置：

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:udid": "emulator-5554",
  "appium:deviceName": "Android Emulator",
  "appium:platformVersion": "16",
  "appium:noReset": true,
  "appium:fullReset": false,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 300,
  "appium:adbExecTimeout": 120000,
  "appium:uiautomator2ServerInstallTimeout": 120000,
  "appium:uiautomator2ServerLaunchTimeout": 120000,
  "appium:remoteAdbHost": "host.docker.internal",
  "appium:remoteAdbPort": 5037
}
```

3. **点击 "Start Session"** 开始连接

### 方案2：使用桌面版 Appium Inspector（需要重启服务）

如果必须使用桌面版 Appium Inspector，需要重启 Appium 服务以添加 `--allow-cors` 参数：

1. **停止 Appium 服务**：
```bash
docker-compose stop appium
```

2. **重新构建并启动**（已更新 Dockerfile）：
```bash
docker-compose build appium
docker-compose up -d appium
```

3. **等待服务启动**（约 30 秒）：
```bash
docker-compose logs -f appium
```

4. **在桌面版 Appium Inspector 中配置**：
   - Remote Host: `localhost` 或 `127.0.0.1`
   - Remote Port: `4723`
   - Remote Path: `/`
   - Desired Capabilities: 使用上面的 JSON 配置

### 方案3：验证连接

测试 Appium 服务是否正常运行：

```bash
# 检查服务状态
docker-compose ps appium

# 检查服务健康状态
curl http://localhost:4723/status

# 查看服务日志
docker-compose logs appium
```

## 📋 连接配置总结

### Appium Server 配置
- **Remote Host**: `localhost` 或 `127.0.0.1`
- **Remote Port**: `4723`
- **Remote Path**: `/` (Appium 3.x 不需要 `/wd/hub`)

### Desired Capabilities (JSON)
```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:udid": "emulator-5554",
  "appium:deviceName": "Android Emulator",
  "appium:platformVersion": "16",
  "appium:noReset": true,
  "appium:fullReset": false,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 300,
  "appium:adbExecTimeout": 120000,
  "appium:uiautomator2ServerInstallTimeout": 120000,
  "appium:uiautomator2ServerLaunchTimeout": 120000,
  "appium:remoteAdbHost": "host.docker.internal",
  "appium:remoteAdbPort": 5037
}
```

## 🔍 故障排查

### 1. 检查 Appium 服务是否运行
```bash
docker-compose ps appium
```
应该显示 `Up` 状态。

### 2. 检查端口是否可访问
```bash
curl http://localhost:4723/status
```
应该返回 JSON 响应，包含 `"ready": true`。

### 3. 检查防火墙设置
确保本地防火墙没有阻止 4723 端口的访问。

### 4. 检查 Docker 网络
如果使用 Docker Desktop，确保端口映射正确：
```bash
docker-compose ps appium
```
应该显示 `0.0.0.0:4723->4723/tcp`。

## 💡 推荐方案

**强烈推荐使用浏览器版 Appium Inspector**（方案1），因为：
- ✅ 无需额外安装
- ✅ 无需配置 CORS
- ✅ 功能完整
- ✅ 更新及时

只需访问 `http://localhost:4723/inspector` 即可使用。
