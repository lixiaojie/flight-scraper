# Appium API 修复指南

## 🔧 修复的问题

### 1. 导入路径问题
**问题**: `ModuleNotFoundError: No module named 'appium.webdriver.common.by'`

**解决方案**: 移除了过时的导入
```python
# ❌ 错误的导入
from appium.webdriver.common.by import By

# ✅ 正确的导入
from appium.webdriver.common.appiumby import AppiumBy
```

### 2. WebDriver初始化问题
**问题**: `missing 1 required keyword-only argument: 'options'`

**解决方案**: 使用新的Options API
```python
# ❌ 旧的方式
desired_caps = {
    'platformName': 'Android',
    'appium:automationName': 'UiAutomator2',
    # ...
}
driver = webdriver.Remote('http://localhost:4723', desired_caps)

# ✅ 新的方式
from appium.options.android import UiAutomator2Options

options = UiAutomator2Options()
options.platform_name = 'Android'
options.automation_name = 'UiAutomator2'
options.device_name = 'Android Emulator'
options.platform_version = '16'
options.no_reset = True
options.full_reset = False
options.auto_grant_permissions = True
options.new_command_timeout = 300

driver = webdriver.Remote('http://localhost:4723', options=options)
```

### 3. 应用启动方法问题
**问题**: `'WebDriver' object has no attribute 'start_activity'`

**解决方案**: 使用新的应用激活方法
```python
# ❌ 旧的方式
driver.start_activity("com.MobileTicket", ".MainActivity")

# ✅ 新的方式
driver.activate_app("com.MobileTicket")
```

## 📋 修复后的脚本

### 主要脚本
- `scripts/flight_scraper_12306.py` - 完整抓取脚本
- `scripts/test_flight_scraper.py` - 测试脚本
- `scripts/test_environment.py` - 环境测试脚本

### 快速测试
```bash
# 快速测试脚本
./scripts/quick_test.sh

# 或手动运行
source flight_scraper_env/bin/activate && python3 scripts/test_flight_scraper.py
```

## 🎯 测试结果

### 成功测试的项目
- ✅ Python模块导入正常
- ✅ Appium服务器连接正常
- ✅ Android设备连接正常
- ✅ Appium连接测试通过
- ✅ 页面源码提取成功
- ✅ 航班信息解析成功

### 提取的航班信息示例
```
找到航班号: ['CZ3568', 'MU5332', 'ZH9511', 'ZH9511', 'CZ3965']
找到时间: ['06:30', '08:50', '07:15', '09:40', '07:45', '10:20', '08:00', '10:25', '10:25', '08:05']
找到价格: ['1', '0', '8', '0', '0']
```

## 🚀 使用方法

### 1. 环境准备
```bash
# 确保Appium服务器运行
./scripts/start_appium_inspector_fixed.sh

# 确保Android设备连接
adb devices
```

### 2. 运行测试
```bash
# 快速测试
./scripts/quick_test.sh

# 完整抓取
source flight_scraper_env/bin/activate && python3 scripts/flight_scraper_12306.py
```

### 3. 输出文件
- `test_page_source.xml` - 测试页面源码
- `flight_page_source_YYYYMMDD_HHMMSS.xml` - 完整页面源码
- `flight_data_YYYYMMDD_HHMMSS.txt` - 解析后的航班数据

## 🔍 故障排除

### 常见问题

#### 1. 模块导入错误
```bash
# 确保在虚拟环境中运行
source flight_scraper_env/bin/activate
```

#### 2. Appium连接失败
```bash
# 检查Appium服务器状态
curl http://localhost:4723/status

# 重启Appium服务器
./scripts/start_appium_inspector_fixed.sh
```

#### 3. Android设备未连接
```bash
# 检查设备连接
adb devices

# 启动Android模拟器
emulator -avd <AVD_NAME> -gpu host
```

## 📚 相关资源

- [Appium Python Client 5.x 文档](https://github.com/appium/python-client)
- [UiAutomator2 驱动文档](http://appium.io/docs/en/drivers/android-uiautomator2/)
- [Selenium WebDriver 文档](https://selenium-python.readthedocs.io/)
