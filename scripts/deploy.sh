#!/bin/bash

# 航班抓取系统一键部署脚本
# 支持 macOS 和 Linux 系统

set -e

echo "🚀 航班抓取系统一键部署脚本"
echo "================================"

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "📱 检测到操作系统: $OS"

# 检查必要的工具
echo "🔍 检查系统依赖..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    if [ "$OS" == "macos" ]; then
        echo "   下载地址: https://www.docker.com/products/docker-desktop"
    else
        echo "   Ubuntu/Debian: sudo apt install docker.io docker-compose"
        echo "   CentOS/RHEL: sudo yum install docker docker-compose"
    fi
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安装"

# 检查 Node.js (用于 Appium)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js (推荐版本 16+)"
    echo "   访问: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"

# 检查 Java (用于 Appium)
if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装，请先安装 Java 11+"
    if [ "$OS" == "macos" ]; then
        echo "   使用 Homebrew: brew install openjdk@11"
    else
        echo "   Ubuntu/Debian: sudo apt install openjdk-11-jdk"
        echo "   CentOS/RHEL: sudo yum install java-11-openjdk-devel"
    fi
    exit 1
fi

echo "✅ Java 版本: $(java -version 2>&1 | head -n 1)"

# 检查 ADB
if ! command -v adb &> /dev/null; then
    echo "⚠️  ADB 未安装，请安装 Android SDK Platform Tools"
    if [ "$OS" == "macos" ]; then
        echo "   使用 Homebrew: brew install android-platform-tools"
    else
        echo "   Ubuntu/Debian: sudo apt install android-tools-adb"
        echo "   CentOS/RHEL: sudo yum install android-tools"
    fi
    echo "   或者从 https://developer.android.com/studio/releases/platform-tools 下载"
fi

echo ""
echo "📦 开始部署..."

# 1. 安装 Appium
echo "1️⃣ 安装 Appium..."
if [ -f "./scripts/install_appium.sh" ]; then
    chmod +x ./scripts/install_appium.sh
    ./scripts/install_appium.sh
else
    echo "❌ Appium 安装脚本不存在"
    exit 1
fi

# 2. 构建 Docker 镜像
echo ""
echo "2️⃣ 构建 Docker 镜像..."
docker-compose build

# 3. 启动服务
echo ""
echo "3️⃣ 启动服务..."
docker-compose up -d

# 4. 等待服务启动
echo ""
echo "4️⃣ 等待服务启动..."
sleep 10

# 5. 检查服务状态
echo ""
echo "5️⃣ 检查服务状态..."
docker-compose ps

# 6. 检查服务健康状态
echo ""
echo "6️⃣ 检查服务健康状态..."

# 检查 Web 服务
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Web 服务运行正常"
else
    echo "❌ Web 服务启动失败"
fi

# 检查 Frontend 服务
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend 服务运行正常"
else
    echo "❌ Frontend 服务启动失败"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 服务访问地址:"
echo "   - Web API: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - API 文档: http://localhost:8000/docs"
echo ""
echo "📱 Appium 服务:"
echo "   - 启动: ./scripts/start_appium.sh"
echo "   - 状态: curl http://localhost:4723/status"
echo ""
echo "🔧 管理命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo ""
echo "📖 使用说明:"
echo "1. 启动 Android 模拟器或连接 Android 设备"
echo "2. 运行: ./scripts/start_appium.sh"
echo "3. 访问: http://localhost:3000"
echo ""
echo "⚠️  注意事项:"
echo "- 确保 Android 模拟器或设备已连接"
echo "- 确保 ADB 可以检测到设备: adb devices"
echo "- 首次使用需要安装 Appium 驱动"