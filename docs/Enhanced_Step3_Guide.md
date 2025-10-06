# 增强版步骤3 - 空铁联运按钮查找指南

## 🔄 循环重试机制

### 功能概述
步骤3现在包含智能循环重试机制，当找不到空铁联运按钮时会：
1. 自动退回到步骤2（检查主页面）
2. 最多重试5次
3. 失败后自动截图并保存页面源码

### 循环流程
```
步骤3: 点击空铁联运按钮
├── 尝试1: 查找空铁联运按钮
│   ├── 成功 → 继续执行
│   └── 失败 → 退回到步骤2 → 等待3秒 → 尝试2
├── 尝试2: 查找空铁联运按钮
│   ├── 成功 → 继续执行
│   └── 失败 → 退回到步骤2 → 等待3秒 → 尝试3
├── ...
└── 尝试5: 查找空铁联运按钮
    ├── 成功 → 继续执行
    └── 失败 → 截图并退出
```

## 📸 错误处理

### 自动截图
当5次尝试都失败时，脚本会：
1. **截图保存**: `flight_scraper_error_YYYYMMDD_HHMMSS.png`
2. **页面源码保存**: `flight_scraper_error_YYYYMMDD_HHMMSS.xml`
3. **自动退出**: 关闭驱动并结束脚本

### 截图文件命名
- **错误截图**: `flight_scraper_error_20250104_143022.png`
- **测试截图**: `test_error_20250104_143022.png`
- **页面源码**: `flight_scraper_error_20250104_143022.xml`

## 🚀 使用方法

### 运行增强版脚本
```bash
# 完整抓取脚本（带循环重试）
source flight_scraper_env/bin/activate && python3 scripts/flight_scraper_12306.py

# 测试脚本（带循环重试）
source flight_scraper_env/bin/activate && python3 scripts/test_flight_scraper.py
```

### 快速测试
```bash
# 一键测试
./scripts/quick_test.sh
```

## 📊 输出示例

### 成功情况
```
🚄 步骤3: 点击空铁联运按钮
🔄 尝试 1/5
✅ 空铁联运按钮已点击
⏳ 等待 5 秒...
```

### 失败情况（5次重试）
```
🚄 步骤3: 点击空铁联运按钮
🔄 尝试 1/5
⚠️ 第1次尝试：空铁联运按钮未找到
🔄 退回到步骤2，重新检查主页面...
✅ 主页面容器已找到
⏳ 等待 3 秒...

🔄 尝试 2/5
⚠️ 第2次尝试：空铁联运按钮未找到
🔄 退回到步骤2，重新检查主页面...
✅ 主页面容器已找到
⏳ 等待 3 秒...

...

🔄 尝试 5/5
⚠️ 第5次尝试：空铁联运按钮未找到
❌ 5次尝试后仍未找到空铁联运按钮

📸 截图并退出 - 原因: 空铁联运按钮未找到
📸 截图已保存: flight_scraper_error_20250104_143022.png
📄 页面源码已保存: flight_scraper_error_20250104_143022.xml
🔚 脚本结束
```

## 🔧 配置参数

### 可调整参数
```python
max_attempts = 5          # 最大重试次数
wait_time = 3             # 重试间隔时间（秒）
step_wait_time = 5        # 步骤间等待时间（秒）
```

### 修改重试次数
在脚本中修改 `max_attempts` 变量：
```python
max_attempts = 3  # 改为3次重试
```

## 📁 输出文件

### 成功执行
- `flight_page_source_YYYYMMDD_HHMMSS.xml` - 页面源码
- `flight_data_YYYYMMDD_HHMMSS.txt` - 航班数据

### 失败执行
- `flight_scraper_error_YYYYMMDD_HHMMSS.png` - 错误截图
- `flight_scraper_error_YYYYMMDD_HHMMSS.xml` - 错误页面源码

## 🔍 故障排除

### 常见问题

#### 1. 空铁联运按钮始终找不到
**可能原因**:
- 12306应用未正确安装
- 应用界面版本不同
- 元素定位器需要更新

**解决方案**:
1. 检查截图文件，确认当前页面状态
2. 查看页面源码，分析实际元素结构
3. 更新元素定位器

#### 2. 主页面检查失败
**可能原因**:
- 应用启动失败
- 页面加载超时
- 元素ID变化

**解决方案**:
1. 确认12306应用已正确安装
2. 检查应用是否正常启动
3. 更新主页面元素定位器

#### 3. 循环重试无效
**可能原因**:
- 网络问题导致页面加载失败
- 应用崩溃或卡死
- 设备连接问题

**解决方案**:
1. 检查网络连接
2. 重启Android模拟器
3. 重启Appium服务器

## 📚 相关文件

- **主脚本**: `scripts/flight_scraper_12306.py`
- **测试脚本**: `scripts/test_flight_scraper.py`
- **快速测试**: `scripts/quick_test.sh`
- **使用指南**: `docs/Flight_Scraper_Guide.md`
- **API修复**: `docs/Appium_API_Fixes.md`
