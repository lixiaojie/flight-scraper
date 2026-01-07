#!/bin/bash
# 运行城市选择功能测试脚本

# 设置默认值
export TEST_FROM_CITY=${TEST_FROM_CITY:-"北京"}
export TEST_TO_CITY=${TEST_TO_CITY:-"上海"}
export SCRAPER_DEVICE_UDID=${SCRAPER_DEVICE_UDID:-"emulator-5554"}
export APPIUM_SERVER_URL=${APPIUM_SERVER_URL:-"http://localhost:4723"}

# 如果使用Docker环境，可能需要不同的配置
if [ -n "$DOCKER_ENV" ]; then
    export APPIUM_SERVER_URL=${APPIUM_SERVER_URL:-"http://appium:4723"}
fi

echo "🚀 开始运行城市选择功能测试"
echo "=================================="
echo "📋 测试配置:"
echo "  出发城市: $TEST_FROM_CITY"
echo "  到达城市: $TEST_TO_CITY"
echo "  设备UDID: $SCRAPER_DEVICE_UDID"
echo "  Appium服务器: $APPIUM_SERVER_URL"
echo "=================================="
echo ""

# 切换到脚本目录
cd "$(dirname "$0")"

# 运行测试脚本
python3 test_city_selection.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ 测试完成"
else
    echo ""
    echo "❌ 测试失败，退出码: $exit_code"
fi

exit $exit_code






