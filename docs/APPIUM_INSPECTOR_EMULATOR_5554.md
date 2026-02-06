# Appium Inspector 连接 emulator-5554 配置指南

## 🎯 连接配置

### 1. Appium Server 配置

在 Appium Inspector 中配置以下服务器信息：

- **Remote Host**: `localhost` 或 `127.0.0.1`
- **Remote Port**: `4723`
- **Remote Path**: `/` (Appium 3.x 不需要 `/wd/hub`)

> **注意**: 如果 Appium 在 Docker 中运行，端口已经映射到主机，所以使用 `localhost:4723` 即可。

---

## 📋 Desired Capabilities 配置

### JSON 格式配置（推荐 - Docker 环境）

在 Appium Inspector 的 **Desired Capabilities** 标签页中，粘贴以下 JSON 配置：

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

> **重要**: 由于 Appium 运行在 Docker 容器中，而 ADB 运行在主机上，**必须**添加 `appium:remoteAdbHost` 和 `appium:remoteAdbPort` 配置，否则 Appium 无法找到设备。

### 如果 ADB 在主机上运行（Docker 环境）

如果你的 ADB 服务器运行在主机上（而非容器内），**这是当前项目的默认配置**，必须添加远程 ADB 配置：

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

**注意**: 如果缺少 `appium:remoteAdbHost` 和 `appium:remoteAdbPort`，会出现错误：
```
Could not find a connected Android device in 20000ms
```

---

## 🔍 关键配置项说明

### 必需配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `platformName` | `Android` | 平台名称 |
| `appium:automationName` | `UiAutomator2` | Android 自动化驱动 |
| `appium:udid` | `emulator-5554` | 设备唯一标识符 |

### 推荐配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `appium:deviceName` | `Android Emulator` | 设备名称（显示用） |
| `appium:platformVersion` | `16` | Android 版本（根据实际调整） |
| `appium:noReset` | `true` | 不重置应用状态 |
| `appium:fullReset` | `false` | 不完全重置 |
| `appium:autoGrantPermissions` | `true` | 自动授权权限 |

### 超时配置（避免连接超时）

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `appium:newCommandTimeout` | `300` | 新命令超时（秒） |
| `appium:adbExecTimeout` | `120000` | ADB 执行超时（毫秒） |
| `appium:uiautomator2ServerInstallTimeout` | `120000` | UiAutomator2 服务安装超时（毫秒） |
| `appium:uiautomator2ServerLaunchTimeout` | `120000` | UiAutomator2 服务启动超时（毫秒） |

### Docker 环境专用配置

如果 Appium 在 Docker 中运行，但 ADB 在主机上：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `appium:remoteAdbHost` | `host.docker.internal` | 远程 ADB 主机地址 |
| `appium:remoteAdbPort` | `5037` | 远程 ADB 端口 |

---

## 🚀 使用步骤

### 1. 确认设备连接

首先确认 emulator-5554 已连接：

```bash
adb devices
```

输出应该包含：
```
emulator-5554    device
```

### 2. 启动 Appium Inspector

1. 打开 Appium Inspector 应用
2. 在 **Remote Host** 中输入: `localhost`
3. 在 **Remote Port** 中输入: `4723`
4. 在 **Remote Path** 中留空或输入: `/`

### 3. 配置 Desired Capabilities

1. 点击 **Desired Capabilities** 标签
2. 粘贴上述 JSON 配置
3. 根据你的实际 Android 版本调整 `platformVersion`

### 4. 启动会话

1. 点击 **Start Session** 按钮
2. 等待连接建立（可能需要几秒钟）
3. 连接成功后，会显示设备屏幕和元素树

---

## 🔧 故障排除

### 问题1: 连接失败 - 设备未找到

**解决方法**:
```bash
# 检查设备是否在线
adb devices

# 如果设备显示为 offline，尝试重启 ADB
adb kill-server
adb start-server
adb devices
```

### 问题2: 连接超时

**解决方法**:
- 增加超时配置值（如上面的配置示例）
- 检查 Appium 服务是否正常运行：
  ```bash
  curl http://localhost:4723/status
  ```

### 问题3: ADB 连接问题（Docker 环境）

**解决方法**:
- 如果 ADB 在主机上运行，确保添加 `remoteAdbHost` 和 `remoteAdbPort` 配置
- 检查 Docker 网络配置，确保 Appium 容器可以访问 `host.docker.internal`

### 问题4: UiAutomator2 服务安装失败

**解决方法**:
- 增加 `uiautomator2ServerInstallTimeout` 和 `uiautomator2ServerLaunchTimeout` 的值
- 检查设备是否有足够的存储空间
- 尝试在设备上手动卸载并重新安装 UiAutomator2 相关应用

---

## 📝 简化配置（最小必需项）

如果只想快速连接，可以使用最小配置：

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:udid": "emulator-5554"
}
```

然后根据实际需要添加其他配置项。

---

## 🔗 相关资源

- 项目中的实际配置: `scripts/config/scraper.config.json`
- 连接代码示例: `scripts/device_connection.py`
- Appium 官方文档: https://appium.io/docs/en/latest/
