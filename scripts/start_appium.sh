#!/bin/bash

# Appium 启动脚本

set -e

echo "🚀 启动 Appium 服务器..."

# 检查 Appium 是否已安装
if ! command -v appium &> /dev/null; then
    echo "❌ Appium 未安装，请先运行: ./scripts/install_appium.sh"
    exit 1
fi

# 检查端口是否被占用
if lsof -iTCP:4723 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "⚠️  端口 4723 已被占用，尝试停止现有进程..."
    pkill -f "appium" || true
    sleep 2
fi

# 设置环境变量
export APPIUM_LOG_LEVEL=info
export APPIUM_RELAXED_SECURITY=true

# 启动 Appium
echo "📱 启动 Appium 服务器 (端口: 4723)..."
echo "   日志级别: info"
echo "   安全模式: relaxed"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

appium --log-level info --relaxed-security
