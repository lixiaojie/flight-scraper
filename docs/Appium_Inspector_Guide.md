# Appium Inspector 使用指南

## 🎯 概述

Appium Inspector 是一个强大的工具，用于检查和识别Android应用的页面元素布局，帮助编写自动化脚本。

## 🚀 快速启动

### 1. 启动服务
```bash
# 启动Appium Inspector服务
./scripts/start_appium_inspector.sh
```

### 2. 访问界面
打开浏览器访问: http://localhost:4723/inspector

## ⚙️ 配置连接

### 服务器配置
- **Remote Host**: `localhost`
- **Remote Port**: `4723`
- **Remote Path**: `/wd/hub`

### 设备配置
- **Platform Name**: `Android`
- **Automation Name**: `UiAutomator2`
- **Device Name**: `Android Emulator`
- **Platform Version**: `14` (根据你的Android版本调整)

### 可选配置
- **No Reset**: `true` (保持应用状态)
- **Full Reset**: `false` (不完全重置)
- **Auto Grant Permissions**: `true` (自动授权)

## 📱 使用步骤

### 1. 连接设备
1. 确保Android模拟器正在运行
2. 在Inspector界面点击 "Start Session"
3. 等待连接建立

### 2. 检查元素
1. 在设备上操作应用
2. 在Inspector中查看元素树
3. 点击元素查看属性
4. 复制元素定位器

### 3. 录制操作
1. 点击 "Record" 开始录制
2. 在设备上执行操作
3. 查看生成的代码
4. 复制到你的测试脚本中

## 🔧 高级功能

### 元素定位器类型
- **ID**: `resource-id`
- **Class**: `class`
- **XPath**: `xpath`
- **Text**: `text`
- **Content-desc**: `content-desc`

### 常用操作
- **点击**: `click()`
- **输入文本**: `send_keys()`
- **滑动**: `swipe()`
- **等待**: `wait()`

## 🐛 故障排除

### 常见问题

#### 1. 连接失败
```bash
# 检查设备连接
adb devices

# 重启ADB
adb kill-server
adb start-server
```

#### 2. 元素找不到
- 检查元素是否可见
- 等待元素加载完成
- 使用更稳定的定位器

#### 3. 权限问题
```bash
# 检查应用权限
adb shell dumpsys package <package_name>
```

### 依赖更新
```bash
# 更新所有依赖
./scripts/update_appium_dependencies.sh
```

## 📝 示例代码

### Python示例
```python
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy

# 连接配置
desired_caps = {
    'platformName': 'Android',
    'automationName': 'UiAutomator2',
    'deviceName': 'Android Emulator',
    'platformVersion': '14',
    'appPackage': 'com.example.app',
    'appActivity': '.MainActivity'
}

# 创建驱动
driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)

# 查找元素
element = driver.find_element(AppiumBy.ID, 'com.example.app:id/button')
element.click()

# 关闭驱动
driver.quit()
```

### JavaScript示例
```javascript
const { Builder, By } = require('selenium-webdriver');

async function test() {
    const driver = await new Builder()
        .usingServer('http://localhost:4723/wd/hub')
        .withCapabilities({
            platformName: 'Android',
            automationName: 'UiAutomator2',
            deviceName: 'Android Emulator',
            platformVersion: '14'
        })
        .build();

    const element = await driver.findElement(By.id('com.example.app:id/button'));
    await element.click();

    await driver.quit();
}
```

## 🎯 最佳实践

1. **使用稳定的定位器**: 优先使用ID，其次使用XPath
2. **等待元素加载**: 使用显式等待而不是隐式等待
3. **处理动态内容**: 使用相对定位器处理动态元素
4. **错误处理**: 添加适当的异常处理
5. **测试数据**: 使用数据驱动的方法

## 📚 相关资源

- [Appium官方文档](http://appium.io/docs/en/about-appium/intro/)
- [UiAutomator2驱动文档](http://appium.io/docs/en/drivers/android-uiautomator2/)
- [Appium Inspector文档](http://appium.io/docs/en/commands/element/find-elements/)
