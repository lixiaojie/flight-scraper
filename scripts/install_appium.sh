#!/bin/bash

# Appium 安装脚本
# 支持 macOS 和 Linux 系统

set -e

echo "🚀 开始安装 Appium 和相关依赖..."

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

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js (推荐版本 16+)"
    echo "   访问: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "⚠️  Node.js 版本过低 ($(node --version))，推荐使用 16+ 版本"
fi

echo "✅ Node.js 版本: $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "✅ npm 版本: $(npm --version)"

# 检查 Java
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

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 11 ]; then
    echo "⚠️  Java 版本过低 ($(java -version 2>&1 | head -n 1))，推荐使用 11+ 版本"
fi

echo "✅ Java 版本: $(java -version 2>&1 | head -n 1)"

# 检查 Android SDK (可选)
if [ -z "$ANDROID_HOME" ]; then
    echo "⚠️  ANDROID_HOME 环境变量未设置"
    echo "   如果使用 Android 模拟器，请设置 ANDROID_HOME 指向 Android SDK 目录"
    echo "   例如: export ANDROID_HOME=/Users/username/Library/Android/sdk"
else
    echo "✅ ANDROID_HOME: $ANDROID_HOME"
fi

# 安装 Appium
echo "📦 安装 Appium..."
npm install -g appium@2.0.0

# 安装 UiAutomator2 驱动
echo "📦 安装 UiAutomator2 驱动..."
appium driver install uiautomator2

# 安装 XCUITest 驱动 (macOS)
if [ "$OS" == "macos" ]; then
    echo "📦 安装 XCUITest 驱动..."
    appium driver install xcuitest
fi

# 验证安装
echo "🔍 验证安装..."
appium --version
appium driver list

echo "✅ Appium 安装完成！"
echo ""
echo "📋 使用说明:"
echo "1. 启动 Appium 服务器: appium"
echo "2. 默认端口: 4723"
echo "3. 查看状态: curl http://localhost:4723/status"
echo ""
echo "🔧 环境变量设置 (可选):"
echo "export ANDROID_HOME=/path/to/android/sdk"
echo "export JAVA_HOME=/path/to/java"
echo ""
echo "📱 支持的平台:"
if [ "$OS" == "macos" ]; then
    echo "- Android (通过 UiAutomator2)"
    echo "- iOS (通过 XCUITest)"
else
    echo "- Android (通过 UiAutomator2)"
fi
