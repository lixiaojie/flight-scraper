# 12306航班信息抓取自动化脚本使用指南

## 🎯 功能概述

本脚本使用Appium自动化Android应用，抓取12306应用中的航班信息，包括：
- 航空公司
- 航班号
- 起飞时间
- 起飞机场
- 落地时间
- 落地机场
- 价格

## 📋 抓取流程

### 自动化步骤
1. **启动12306应用** - 通过accessibility ID或直接启动
2. **检查主页面** - 验证主页面容器
3. **点击空铁联运** - 进入空铁联运功能
4. **检查空铁联运页面** - 验证页面加载
5. **点击查询按钮** - 触发航班查询
6. **检查航班列表** - 验证航班列表页面
7. **提取页面源码** - 获取完整页面数据
8. **解析航班信息** - 使用lxml和正则表达式提取数据

### 等待时间
- 每个步骤之间等待5秒
- 可根据网络状况调整等待时间

## 🚀 使用方法

### 1. 环境准备

#### 启动Appium服务器
```bash
# 使用修复版启动脚本
./scripts/start_appium_inspector_fixed.sh
```

#### 确保Android设备连接
```bash
adb devices
```

### 2. 运行抓取脚本

#### 完整抓取脚本
```bash
python3 scripts/flight_scraper_12306.py
```

#### 测试脚本
```bash
python3 scripts/test_flight_scraper.py
```

### 3. 输出文件

#### 页面源码文件
- `flight_page_source_YYYYMMDD_HHMMSS.xml` - 完整的页面源码

#### 航班数据文件
- `flight_data_YYYYMMDD_HHMMSS.txt` - 解析后的航班信息

## 🔧 配置说明

### Appium连接配置
```python
desired_caps = {
    'platformName': 'Android',
    'appium:automationName': 'UiAutomator2',
    'appium:deviceName': 'Android Emulator',
    'appium:platformVersion': '16',
    'appium:noReset': True,
    'appium:fullReset': False,
    'appium:autoGrantPermissions': True,
    'appium:newCommandTimeout': 300
}
```

### 元素定位策略

#### 1. 启动12306应用
```python
# 方法1: 通过accessibility ID
app_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "铁路12306")

# 方法2: 直接启动应用
driver.start_activity("com.MobileTicket", ".MainActivity")
```

#### 2. 检查主页面
```python
home_container = driver.find_element(AppiumBy.ID, "com.MobileTicket:id/ticket_home_content_container")
```

#### 3. 点击空铁联运
```python
air_rail_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "空铁联运")
```

#### 4. 检查空铁联运页面
```python
air_rail_page = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("空铁联运首页")')
```

#### 5. 点击查询按钮
```python
search_button = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("查询")')
```

#### 6. 检查航班列表
```python
flight_list = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("航班列表")')
```

## 📊 数据解析

### 航班信息提取

#### 使用lxml解析
```python
from lxml import etree

# 解析XML
root = etree.fromstring(page_source)

# 查找航班元素
flight_elements = root.xpath('//*[contains(@class, "flight") or contains(@text, "航班")]')
```

#### 使用正则表达式提取
```python
import re

# 航班号: CA1234, MU5678
flight_numbers = re.findall(r'([A-Z]{2}\d{3,4})', page_source)

# 时间: 08:30, 14:25
times = re.findall(r'(\d{1,2}:\d{2})', page_source)

# 价格: ¥580, 580元
prices = re.findall(r'[¥￥]?(\d+)元?', page_source)

# 机场代码: PEK, SHA
airports = re.findall(r'([A-Z]{3})', page_source)
```

### 航空公司代码映射
```python
airline_codes = {
    'CA': '中国国际航空',
    'MU': '中国东方航空',
    'CZ': '中国南方航空',
    'HU': '海南航空',
    '3U': '四川航空',
    '9C': '春秋航空',
    'JD': '首都航空',
    'HO': '吉祥航空'
}
```

## 🔍 故障排除

### 常见问题

#### 1. 元素找不到
- **原因**: 页面加载慢或元素ID变化
- **解决**: 增加等待时间或更新元素定位器

#### 2. 应用启动失败
- **原因**: 应用未安装或包名错误
- **解决**: 检查应用是否已安装，确认包名正确

#### 3. 页面源码为空
- **原因**: 页面未完全加载
- **解决**: 增加等待时间或添加显式等待

#### 4. 航班信息解析失败
- **原因**: 页面结构变化或正则表达式不匹配
- **解决**: 更新解析逻辑或检查页面结构

### 调试方法

#### 1. 保存页面源码
```python
# 保存页面源码用于调试
with open("debug_page_source.xml", "w", encoding="utf-8") as f:
    f.write(page_source)
```

#### 2. 截图调试
```python
# 截图保存当前状态
driver.save_screenshot("debug_screenshot.png")
```

#### 3. 元素检查
```python
# 检查所有可点击元素
elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
for element in elements:
    print(f"Button text: {element.text}")
```

## 📈 性能优化

### 1. 等待策略优化
```python
# 使用显式等待替代固定等待
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((AppiumBy.ID, "element_id")))
```

### 2. 批量处理
```python
# 批量查找元素
elements = driver.find_elements(AppiumBy.CLASS_NAME, "flight-item")
for element in elements:
    # 处理每个航班元素
    pass
```

### 3. 内存管理
```python
# 及时清理不需要的数据
del page_source
driver.quit()
```

## 🎯 扩展功能

### 1. 多城市查询
```python
def query_multiple_routes(self, routes):
    """查询多个航线的航班信息"""
    for route in routes:
        self.select_departure_city(route['departure'])
        self.select_arrival_city(route['arrival'])
        self.search_flights()
        flights = self.extract_flight_info()
        self.save_flight_data(flights, route['name'])
```

### 2. 定时抓取
```python
import schedule
import time

def scheduled_scraping():
    """定时抓取航班信息"""
    scraper = FlightScraper12306()
    scraper.run_scraping()

# 每天上午9点执行
schedule.every().day.at("09:00").do(scheduled_scraping)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. 数据存储
```python
import sqlite3

def save_to_database(self, flights):
    """保存航班数据到数据库"""
    conn = sqlite3.connect('flight_data.db')
    cursor = conn.cursor()
    
    for flight in flights:
        cursor.execute("""
            INSERT INTO flights (airline, flight_number, departure_time, 
                               departure_airport, arrival_time, arrival_airport, price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (flight['airline'], flight['flight_number'], flight['departure_time'],
              flight['departure_airport'], flight['arrival_time'], 
              flight['arrival_airport'], flight['price']))
    
    conn.commit()
    conn.close()
```

## 📚 相关资源

- [Appium官方文档](http://appium.io/docs/en/2.0/)
- [UiAutomator2驱动文档](http://appium.io/docs/en/drivers/android-uiautomator2/)
- [Selenium WebDriver文档](https://selenium-python.readthedocs.io/)
- [lxml解析文档](https://lxml.de/parsing.html)
- [正则表达式指南](https://docs.python.org/3/library/re.html)
