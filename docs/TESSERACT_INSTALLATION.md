# Tesseract OCR 安装说明

## ✅ 已完成的配置

### 1. Dockerfile配置
已在以下Dockerfile中添加tesseract OCR安装：

- `backend/backend.Dockerfile` - Web服务
- `backend/scraper.Dockerfile` - 抓取服务

### 2. 安装的组件
- `tesseract-ocr` - Tesseract OCR引擎
- `tesseract-ocr-chi-sim` - 简体中文语言包
- `tesseract-ocr-eng` - 英文语言包

### 3. Python依赖
已在 `backend/requirements.txt` 中添加：
- `Pillow==10.1.0` - 图像处理库
- `pytesseract==0.3.10` - Tesseract Python绑定

## 🔧 重新构建Docker镜像

由于修改了Dockerfile，需要重新构建镜像：

```bash
# 重新构建web服务镜像
docker-compose build web

# 重新构建flight-scraper服务镜像（如果使用）
docker-compose build flight-scraper

# 或者重新构建所有服务
docker-compose build
```

## ✅ 验证安装

构建完成后，可以验证tesseract是否已安装：

```bash
# 进入web容器验证
docker-compose exec web tesseract --version

# 检查语言包
docker-compose exec web tesseract --list-langs
```

应该看到：
- tesseract版本信息
- `chi_sim` 和 `eng` 语言包

## 🚀 使用

重新构建后，OCR功能将自动可用，无需额外配置。

## ⚠️ 注意事项

1. **镜像大小**：安装tesseract会增加镜像大小（约50-100MB）
2. **构建时间**：首次构建可能需要更长时间下载tesseract包
3. **缓存**：如果使用Docker缓存，可能需要清理缓存后重新构建

## 🔍 故障排除

### 如果仍然提示"tesseract is not installed"

1. 确认已重新构建镜像：
   ```bash
   docker-compose build --no-cache web
   ```

2. 确认容器中已安装：
   ```bash
   docker-compose exec web which tesseract
   docker-compose exec web tesseract --version
   ```

3. 检查Python库：
   ```bash
   docker-compose exec web python3 -c "import pytesseract; print(pytesseract.get_tesseract_version())"
   ```

4. 如果问题仍然存在，可能需要重启容器：
   ```bash
   docker-compose restart web
   ```

