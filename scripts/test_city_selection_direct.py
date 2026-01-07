#!/usr/bin/env python3
"""
直接测试城市选择功能（跳过导航步骤）
假设设备已经在空铁联运首页
"""

import time
import os
import sys
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException

# 导入设备连接和城市选择函数
try:
    from device_connection import connect_device
    from test_city_selection import (
        find_city_element,
        click_city_and_enter_selection,
        find_search_box,
        input_city_search,
        select_city_from_results,
        go_back_to_previous_page,
        test_city_selection,
        get_city_pinyin_first_letter
    )
except Exception:
    sys.path.insert(0, os.path.dirname(__file__))
    from device_connection import connect_device
    from test_city_selection import (
        find_city_element,
        click_city_and_enter_selection,
        find_search_box,
        input_city_search,
        select_city_from_results,
        go_back_to_previous_page,
        test_city_selection,
        get_city_pinyin_first_letter
    )


def wait_step(seconds=2):
    """步骤间等待"""
    print(f"⏳ 等待 {seconds} 秒...")
    time.sleep(seconds)


def main():
    """主函数 - 直接测试城市选择功能"""
    driver = None

    try:
        # 连接设备
        print("🔌 连接设备...")
        driver = connect_device()

        print("✅ 设备连接成功")
        print("💡 假设设备已在空铁联运首页，直接开始测试城市选择功能")
        wait_step(3)  # 等待页面稳定

        # 从环境变量获取测试城市，如果没有则使用默认值
        from_city = os.getenv("TEST_FROM_CITY", "北京")
        to_city = os.getenv("TEST_TO_CITY", "上海")

        print(f"📋 测试配置: 出发城市={from_city}, 到达城市={to_city}")
        print("\n" + "=" * 60)

        # 执行城市选择测试
        success = test_city_selection(driver, from_city, to_city)

        # 测试完成后，保持设备停留在当前页面
        print("\n📱 测试完成，设备将停留在当前页面")
        print("💡 提示: 可以手动检查城市选择结果")
        print("💡 提示: 按 Ctrl+C 退出（不会关闭驱动）")

        # 保持连接，等待用户中断
        try:
            while True:
                time.sleep(10)
                print("⏳ 设备保持连接中...（按 Ctrl+C 退出）")
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出测试")

        return success

    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 注意：根据需求，测试完成后不关闭驱动，保持设备停留在页面
        pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

