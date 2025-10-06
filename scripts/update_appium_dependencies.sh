#!/bin/bash

echo "🔄 更新 Appium 依赖库"
echo "====================="

# 检查Node.js版本
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📋 检查Node.js版本..."
node --version
npm --version

# 更新npm到最新版本
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🔄 更新npm..."
npm install -g npm@latest

# 清理npm缓存
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🧹 清理npm缓存..."
npm cache clean --force

# 更新Appium到最新版本
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🚀 更新Appium..."
npm update -g appium

# 更新Appium Inspector插件
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🔍 更新Appium Inspector插件..."
npm install -g appium-inspector-plugin@latest

# 更新UiAutomator2驱动
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📱 更新UiAutomator2驱动..."
appium driver update uiautomator2

# 更新XCUITest驱动
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🍎 更新XCUITest驱动..."
appium driver update xcuitest

# 检查依赖状态
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📊 检查依赖状态..."
echo ""
echo "Appium版本:"
appium --version

echo ""
echo "已安装的驱动:"
appium driver list --installed

echo ""
echo "已安装的插件:"
appium plugin list --installed

echo ""
echo "npm过时包检查:"
npm outdated -g --depth=0 | grep -E "(appium|inspector)" || echo "所有Appium相关包都是最新版本"

echo ""
echo "✅ Appium依赖更新完成！"
echo "========================"
echo "现在可以运行: docker-compose up -d appium"
