#!/bin/bash

echo "🛑 停止航班结果系统"
echo "=================="

# 停止前端服务
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🎨 停止前端服务..."
FRONTEND_PID=$(lsof -t -i:3000)
if [ ! -z "$FRONTEND_PID" ]; then
    kill -9 $FRONTEND_PID
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 前端服务已停止"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️ 前端服务未运行"
fi

# 停止后端服务
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🚀 停止后端服务..."
BACKEND_PID=$(lsof -t -i:8000)
if [ ! -z "$BACKEND_PID" ]; then
    kill -9 $BACKEND_PID
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 后端服务已停止"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️ 后端服务未运行"
fi

# 停止Appium服务
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📱 停止Appium服务..."
APPIUM_PID=$(lsof -t -i:4723)
if [ ! -z "$APPIUM_PID" ]; then
    kill -9 $APPIUM_PID
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ Appium服务已停止"
else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️ Appium服务未运行"
fi

echo ""
echo "✅ 所有服务已停止"
echo "=================="
