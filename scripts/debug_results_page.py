#!/usr/bin/env python3
"""
调试脚本：连接设备并检查结果页状态，测试滚动和提取逻辑
"""
from page_capture import (
    extract_flight_elements_from_xml,
    swipe_down_in_middle,
    swipe_up_in_middle,
    find_scrollable_list,
    scroll_to_top
)
from device_connection import connect_device
import sys
import os
import time
from datetime import datetime

# 添加scripts目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def debug_results_page():
    """调试结果页的滚动和提取逻辑"""
    driver = None

    try:
        print("🔌 连接设备...")
        driver = connect_device()
        print("✅ 设备连接成功\n")

        # 等待页面稳定
        print("⏳ 等待3秒，确保页面已加载...")
        time.sleep(3)

        # 检查当前页面
        print("🔍 检查当前页面状态...")
        try:
            current_activity = driver.current_activity
            print(f"📱 当前Activity: {current_activity}")
        except Exception as e:
            print(f"⚠️ 无法获取Activity: {e}")

        # 获取初始页面源码
        print("\n📄 获取初始页面源码...")
        initial_page_source = driver.page_source
        print(f"✅ 页面源码长度: {len(initial_page_source)} 字符")

        # 提取初始航班信息
        print("\n🔍 提取初始航班信息...")
        initial_flights, initial_elements, initial_count = extract_flight_elements_from_xml(
            initial_page_source, driver=None)
        print(f"📊 初始状态:")
        print(f"  - 元素数量: {initial_count}")
        print(f"  - 唯一元素文本数: {len(initial_elements)}")
        print(f"  - 唯一航班数: {len(initial_flights)}")
        if initial_flights:
            print(f"  - 航班号: {sorted(initial_flights)}")

        # 查找可滚动元素
        print("\n🔍 查找可滚动元素...")
        scrollable_info = find_scrollable_list(driver)
        if scrollable_info:
            print(f"✅ 找到可滚动元素: {scrollable_info}")
        else:
            print("⚠️ 未找到可滚动元素，将使用页面中间区域")

        # 滚动到顶部
        print("\n🔄 滚动到页面顶部...")
        scroll_to_top(driver)
        time.sleep(2)

        # 测试向下滚动（加载更多内容）
        print("\n🧪 测试向下滚动（加载更多航班）...")
        print("📍 执行向下滑动（从上往下，显示下面的内容）...")
        swipe_down_in_middle(driver, scrollable_info)
        time.sleep(3)  # 等待内容加载

        # 获取滚动后的页面源码
        print("\n📄 获取滚动后的页面源码...")
        after_scroll_page_source = driver.page_source
        print(f"✅ 页面源码长度: {len(after_scroll_page_source)} 字符")

        # 提取滚动后的航班信息
        print("\n🔍 提取滚动后的航班信息...")
        after_flights, after_elements, after_count = extract_flight_elements_from_xml(
            after_scroll_page_source, driver=None)
        print(f"📊 滚动后状态:")
        print(f"  - 元素数量: {after_count}")
        print(f"  - 唯一元素文本数: {len(after_elements)}")
        print(f"  - 唯一航班数: {len(after_flights)}")
        if after_flights:
            print(f"  - 航班号: {sorted(after_flights)}")

        # 比较差异
        print("\n📊 比较滚动前后差异:")
        new_flights = after_flights - initial_flights
        new_elements = after_elements - initial_elements
        print(f"  - 新增航班数: {len(new_flights)}")
        if new_flights:
            print(f"  - 新增航班号: {sorted(new_flights)}")
        print(f"  - 新增元素数: {len(new_elements)}")

        # 如果向下滚动没有新内容，尝试向上滚动
        if len(new_flights) == 0 and len(new_elements) == 0:
            print("\n⚠️ 向下滚动未发现新内容，尝试向上滚动...")
            swipe_up_in_middle(driver, scrollable_info)
            time.sleep(3)

            up_page_source = driver.page_source
            up_flights, up_elements, up_count = extract_flight_elements_from_xml(
                up_page_source, driver=None)
            print(f"📊 向上滚动后状态:")
            print(f"  - 唯一航班数: {len(up_flights)}")
            if up_flights:
                print(f"  - 航班号: {sorted(up_flights)}")

            up_new_flights = up_flights - initial_flights
            if up_new_flights:
                print(f"  - 向上滚动发现新航班: {sorted(up_new_flights)}")

        # 保存页面源码用于分析
        print("\n💾 保存页面源码...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(output_dir, exist_ok=True)

        initial_file = os.path.join(
            output_dir, f"debug_initial_{timestamp}.xml")
        after_file = os.path.join(
            output_dir, f"debug_after_scroll_{timestamp}.xml")

        with open(initial_file, 'w', encoding='utf-8') as f:
            f.write(initial_page_source)
        print(f"✅ 初始页面源码已保存: {initial_file}")

        with open(after_file, 'w', encoding='utf-8') as f:
            f.write(after_scroll_page_source)
        print(f"✅ 滚动后页面源码已保存: {after_file}")

        print("\n✅ 调试完成！")
        print("💡 提示: 检查保存的XML文件以分析页面结构")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n📱 保持连接，按 Ctrl+C 退出...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 退出")
                # 不关闭driver，让用户手动关闭


if __name__ == "__main__":
    debug_results_page()
