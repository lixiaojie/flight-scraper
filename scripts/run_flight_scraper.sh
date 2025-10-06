#!/bin/bash

echo "🚀 12306航班信息抓取自动化脚本"
echo "================================"

# 检查Appium服务器状态
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🔍 检查Appium服务器状态..."
if ! curl -s http://localhost:4723/status > /dev/null; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ Appium服务器未运行"
    echo "请先启动Appium服务器:"
    echo "  docker-compose up -d appium"
    exit 1
fi
echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ Appium服务器运行正常"

# 检查Android设备连接
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📱 检查Android设备连接..."
if ! adb devices | grep -q "device$"; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ 未找到Android设备"
    echo "请确保Android模拟器已启动:"
    echo "  emulator -avd <AVD_NAME> -gpu host"
    exit 1
fi
echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ Android设备已连接"
adb devices

# 检查Python环境
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🐍 检查Python环境..."
if [ ! -d "flight_scraper_env" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] 📦 创建Python虚拟环境..."
    python3 -m venv flight_scraper_env
    source flight_scraper_env/bin/activate
    pip install lxml Appium-Python-Client
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 虚拟环境创建完成"
else
    source flight_scraper_env/bin/activate
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ 虚拟环境已存在"
fi

# 选择运行模式
echo ""
echo "请选择运行模式:"
echo "1. 完整抓取脚本 (推荐)"
echo "2. 测试脚本"
echo "3. 退出"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🚀 启动完整抓取脚本..."
        python3 scripts/flight_scraper_12306.py
        ;;
    2)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 🧪 启动测试脚本..."
        python3 scripts/test_flight_scraper.py
        ;;
    3)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 👋 退出"
        exit 0
        ;;
    *)
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 脚本执行完成！"
echo "📁 输出文件:"
echo "  - flight_page_source_*.xml (页面源码)"
echo "  - flight_data_*.txt (航班数据)"
echo "  - test_page_source.xml (测试页面源码)"
echo ""
echo "📋 使用说明:"
echo "1. 查看航班数据文件了解抓取结果"
echo "2. 如有问题，请检查页面源码文件"
echo "3. 参考 docs/Flight_Scraper_Guide.md 了解详细用法"
