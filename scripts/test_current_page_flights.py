#!/usr/bin/env python3
"""
测试脚本：连接设备并统计当前页面可以抓取到的航班数量
"""
from page_capture import (
    extract_flight_elements_from_xml,
    smart_scroll_and_capture
)
from device_connection import connect_device
import sys
import os
import time
from datetime import datetime

# 添加scripts目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_current_page_flights():
    """测试当前页面的航班抓取"""
    driver = None

    try:
        print("=" * 60)
        print("🔌 连接设备...")
        print("=" * 60)
        driver = connect_device()
        print("✅ 设备连接成功\n")

        # 等待页面稳定
        print("⏳ 等待3秒，确保页面已加载...")
        time.sleep(3)

        # 检查当前页面
        print("\n" + "=" * 60)
        print("🔍 检查当前页面状态...")
        print("=" * 60)
        try:
            current_activity = driver.current_activity
            print(f"📱 当前Activity: {current_activity}")
        except Exception as e:
            print(f"⚠️ 无法获取Activity: {e}")

        # 获取初始页面源码（不滚动）
        print("\n" + "=" * 60)
        print("📄 获取初始页面源码（不滚动）...")
        print("=" * 60)
        initial_page_source = driver.page_source
        print(f"✅ 页面源码长度: {len(initial_page_source)} 字符")

        # 提取初始航班信息
        print("\n🔍 提取初始航班信息...")
        initial_flights, initial_elements, initial_count = extract_flight_elements_from_xml(
            initial_page_source, driver=None)
        print(f"\n📊 初始状态（不滚动）:")
        print(f"  - 可见元素数量: {initial_count}")
        print(f"  - 唯一元素文本数: {len(initial_elements)}")
        print(f"  - 唯一航班数: {len(initial_flights)}")
        if initial_flights:
            print(f"  - 航班号列表: {sorted(initial_flights)}")
        else:
            print("  - ⚠️ 未找到航班号")

        # 执行智能滚动并抓取
        print("\n" + "=" * 60)
        print("🔄 执行智能滚动以加载所有航班...")
        print("=" * 60)
        output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(output_dir, exist_ok=True)

        final_page_source, _ = smart_scroll_and_capture(driver, output_dir)

        # 提取最终航班信息
        print("\n" + "=" * 60)
        print("🔍 提取滚动后的最终航班信息...")
        print("=" * 60)
        final_flights, final_elements, final_count = extract_flight_elements_from_xml(
            final_page_source, driver=None)

        print(f"\n📊 最终状态（滚动后）:")
        print(f"  - 可见元素数量: {final_count}")
        print(f"  - 唯一元素文本数: {len(final_elements)}")
        print(f"  - 唯一航班数: {len(final_flights)}")
        if final_flights:
            print(f"  - 航班号列表: {sorted(final_flights)}")
            print(f"\n✅ 成功抓取到 {len(final_flights)} 个航班")
        else:
            print("  - ⚠️ 未找到航班号")

        # 比较差异
        print("\n" + "=" * 60)
        print("📊 滚动前后对比:")
        print("=" * 60)
        new_flights = final_flights - initial_flights
        print(f"  - 初始航班数: {len(initial_flights)}")
        print(f"  - 最终航班数: {len(final_flights)}")
        print(f"  - 新增航班数: {len(new_flights)}")
        if new_flights:
            print(f"  - 新增航班号: {sorted(new_flights)}")

        # 保存结果摘要
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(
            output_dir, f"flight_count_test_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("航班抓取测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                f"测试时间: {
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"初始状态（不滚动）:\n")
            f.write(f"  - 唯一航班数: {len(initial_flights)}\n")
            if initial_flights:
                f.write(f"  - 航班号: {', '.join(sorted(initial_flights))}\n")
            f.write(f"\n最终状态（滚动后）:\n")
            f.write(f"  - 唯一航班数: {len(final_flights)}\n")
            if final_flights:
                f.write(f"  - 航班号: {', '.join(sorted(final_flights))}\n")
            f.write(f"\n新增航班数: {len(new_flights)}\n")
            if new_flights:
                f.write(f"新增航班号: {', '.join(sorted(new_flights))}\n")

        print(f"\n💾 测试结果已保存到: {summary_file}")
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)

        return len(final_flights)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if driver:
            print("\n🔚 关闭设备连接...")
            try:
                driver.quit()
                print("✅ 设备连接已关闭")
            except Exception as e:
                print(f"⚠️ 关闭连接时出错: {e}")


if __name__ == "__main__":
    flight_count = test_current_page_flights()
    print(f"\n🎯 最终统计: 共抓取到 {flight_count} 个航班")
    print("=" * 60)
    print("✅ 测试脚本执行完成，已自动退出")
    print("=" * 60)
