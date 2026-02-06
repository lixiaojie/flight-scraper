# 测试滚动截图OCR识别方法

## 问题
结果页滚动和截图识别方法有问题，实际结果远多于6个，但只识别到6个。

## 测试方法

### 方法1: 在 Docker 容器内运行（推荐）

```bash
# 使用 flight-scraper 服务运行测试脚本
docker-compose run --rm flight-scraper python3 /app/scripts/test_scroll_ocr.py
```

### 方法2: 进入容器后运行

```bash
# 进入 flight-scraper 容器
docker-compose run --rm flight-scraper bash

# 在容器内运行测试脚本
python3 /app/scripts/test_scroll_ocr.py
```

### 方法3: 使用 web 服务运行（如果 web 服务有所有依赖）

```bash
# 进入 web 容器
docker-compose exec web bash

# 在容器内运行测试脚本
python3 /app/scripts/test_scroll_ocr.py
```

## 前提条件

1. **确保设备已停留在结果页**
   - 测试脚本会等待5秒，请在此之前确保设备已停留在结果页

2. **确保 Docker 容器正在运行**
   ```bash
   docker-compose ps
   ```

3. **确保 Appium 服务正常**
   ```bash
   docker-compose ps appium
   ```

## 测试内容

测试脚本会执行以下操作：

1. **连接设备** - 连接到模拟器或真实设备
2. **单次截图识别** - 测试当前页面的OCR识别
3. **滚动识别** - 滚动页面并识别所有航班（最多30次滚动）
4. **保存结果** - 保存OCR文本和截图到 `results/` 目录

## 输出文件

- `test_ocr_text_YYYYMMDD_HHMMSS.txt` - 单次截图的OCR文本
- `test_combined_ocr_YYYYMMDD_HHMMSS.txt` - 所有滚动后的完整OCR文本
- `ocr_scroll_YYYYMMDD_HHMMSS_XX.png` - 滚动过程中的截图（前5张）

## 改进的滚动策略

- **最大滚动次数**: 30次（从15次增加）
- **最小滚动次数**: 5次（从3次增加）
- **连续无新内容容错**: 5次（从3次增加）
- **滚动距离**: 70%-30%（从60%-40%增加）
- **等待时间**: 2.0-2.5秒（从1.0-1.2秒增加）
- **多种滚动方式**: 主要方式失败时自动尝试备用方式

## 故障排查

如果遇到问题：

1. **导入错误**: 确保在 Docker 容器内运行
2. **设备连接失败**: 检查 Appium 服务是否正常运行
3. **OCR识别失败**: 检查 tesseract 是否已安装
4. **滚动无效**: 查看日志，可能需要调整滚动参数
