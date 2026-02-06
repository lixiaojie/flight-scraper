# Appium Inspector 连接 Docker 中 Appium 的配置修复

## 🚨 问题

使用 Appium Inspector 桌面应用连接时出现错误：
```
WebDriverError: Could not find a connected Android device in 20000ms
```

## ✅ 原因

Appium 运行在 Docker 容器中，而 ADB 服务器运行在主机上。如果 Desired Capabilities 中缺少 `remoteAdbHost` 和 `remoteAdbPort` 配置，Appium 无法通过容器访问主机上的 ADB 服务，因此找不到设备。

## 🔧 解决方案

### 正确的 Desired Capabilities 配置

在 Appium Inspector 中，必须使用以下完整配置：

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

### 关键配置项说明

#### ⚠️ 必需配置（Docker 环境）

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `appium:remoteAdbHost` | `host.docker.internal` | **必需** - 告诉 Appium 通过此地址访问主机上的 ADB |
| `appium:remoteAdbPort` | `5037` | **必需** - ADB 服务器的端口 |
| `appium:udid` | `emulator-5554` | **必需** - 设备唯一标识符 |

#### 推荐配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `appium:platformVersion` | `16` | 根据你的 Android 版本调整 |
| `appium:adbExecTimeout` | `120000` | ADB 操作超时（毫秒），避免超时 |
| `appium:uiautomator2ServerInstallTimeout` | `120000` | UiAutomator2 安装超时 |
| `appium:uiautomator2ServerLaunchTimeout` | `120000` | UiAutomator2 启动超时 |

## 🔍 验证步骤

### 1. 检查主机 ADB 连接

```bash
adb devices
```

应该显示：
```
List of devices attached
emulator-5554    device
```

### 2. 检查容器内是否能访问主机 ADB

```bash
docker exec flight-scraper-appium-1 adb -H host.docker.internal -P 5037 devices
```

应该显示相同的设备列表。

### 3. 检查 Appium 服务状态

```bash
curl http://localhost:4723/status
```

应该返回：
```json
{"value":{"ready":true,"message":"The server is ready to accept new connections"}}
```

### 4. 在 Appium Inspector 中测试

1. 打开 Appium Inspector
2. 设置服务器: `localhost:4723`
3. 粘贴上面的完整 JSON 配置
4. 点击 **Start Session**

## 📋 常见问题排查

### 问题1: 仍然提示找不到设备

**解决方法**:
- 确认 `appium:remoteAdbHost` 设置为 `host.docker.internal`
- 确认 `appium:remoteAdbPort` 设置为 `5037`
- 检查主机 ADB 是否正常运行: `adb devices`
- 检查容器网络配置是否正确

### 问题2: 连接超时

**解决方法**:
- 增加超时配置:
  - `appium:adbExecTimeout`: `120000` (或更大)
  - `appium:uiautomator2ServerInstallTimeout`: `120000`
  - `appium:uiautomator2ServerLaunchTimeout`: `120000`

### 问题3: `host.docker.internal` 无法解析

**解决方法**:
- 检查 `docker-compose.yml` 中的 `extra_hosts` 配置:
  ```yaml
  extra_hosts:
    - "host.docker.internal:host-gateway"
  ```

## 🎯 完整配置示例（Appium Inspector）

### 服务器配置
- **Remote Host**: `localhost`
- **Remote Port**: `4723`
- **Remote Path**: `/` (留空)

### Desired Capabilities（JSON）
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

## ✅ 成功标志

连接成功后，你应该看到：
1. ✅ Appium Inspector 显示设备屏幕
2. ✅ 元素树可以正常加载
3. ✅ 可以点击元素查看属性
4. ✅ 可以执行操作（点击、输入等）

## 📚 相关文档

- 基础连接配置: `APPIUM_INSPECTOR_EMULATOR_5554.md`
- Web 界面问题: `APPIUM_INSPECTOR_WEB_FIX.md`
