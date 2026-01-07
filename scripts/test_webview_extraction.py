#!/usr/bin/env python3
"""
测试WebView内容提取：使用JavaScript和OCR混合方式
"""
from page_capture import extract_flight_elements_from_xml, smart_scroll_and_capture
from device_connection import connect_device
import sys
import os
import time
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_webview_extraction():
    """测试WebView内容提取"""
    driver = None

    try:
        print("=" * 60)
        print("🔌 连接设备...")
        print("=" * 60)
        driver = connect_device()
        print("✅ 设备连接成功\n")

        time.sleep(3)

        # 检查当前页面
        try:
            current_activity = driver.current_activity
            print(f"📱 当前Activity: {current_activity}")
        except Exception as e:
            print(f"⚠️ 无法获取Activity: {e}")

        # 检查WebView上下文
        print("\n🔍 检查WebView上下文...")
        try:
            contexts = driver.contexts
            print(f"📱 可用上下文: {contexts}")
            for context in contexts:
                if 'WEBVIEW' in context.upper():
                    print(f"✅ 发现WebView上下文: {context}")
        except Exception as e:
            print(f"⚠️ 检查上下文失败: {e}")

        # 获取页面源码（包含WebView JavaScript提取）
        print("\n" + "=" * 60)
        print("📄 获取页面源码（包含WebView JavaScript提取）...")
        print("=" * 60)
        page_source = driver.page_source
        print(f"✅ 页面源码长度: {len(page_source)} 字符")

        # 提取航班信息（现在包含WebView支持）
        print("\n🔍 提取航班信息（包含WebView JavaScript）...")
        flights, elements, count = extract_flight_elements_from_xml(
            page_source, driver=driver)

        print(f"\n📊 提取结果:")
        print(f"  - 可见元素数量: {count}")
        print(f"  - 唯一元素文本数: {len(elements)}")
        print(f"  - 唯一航班数: {len(flights)}")
        if flights:
            print(f"  - 航班号列表: {sorted(flights)}")
        else:
            print("  - ⚠️ 未找到航班号")

        # 执行滚动并再次提取
        print("\n" + "=" * 60)
        print("🔄 执行滚动并再次提取...")
        print("=" * 60)
        output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(output_dir, exist_ok=True)

        final_page_source, _ = smart_scroll_and_capture(driver, output_dir)

        # 最终提取
        print("\n🔍 最终提取航班信息...")
        final_flights, final_elements, final_count = extract_flight_elements_from_xml(
            final_page_source, driver=driver)

        print(f"\n📊 最终结果:")
        print(f"  - 唯一航班数: {len(final_flights)}")
        if final_flights:
            print(f"  - 航班号列表: {sorted(final_flights)}")
            print(f"\n✅ 总共识别到 {len(final_flights)} 个航班")
        else:
            print("  - ⚠️ 未找到航班号")

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(output_dir, f"webview_test_{timestamp}.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("WebView提取测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                f"测试时间: {
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"初始提取:\n")
            f.write(f"  - 唯一航班数: {len(flights)}\n")
            if flights:
                f.write(f"  - 航班号: {', '.join(sorted(flights))}\n")
            f.write(f"\n最终提取（滚动后）:\n")
            f.write(f"  - 唯一航班数: {len(final_flights)}\n")
            if final_flights:
                f.write(f"  - 航班号: {', '.join(sorted(final_flights))}\n")

        print(f"\n💾 结果已保存到: {result_file}")

        return len(final_flights)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        if driver:
            driver.quit()
            print("\n✅ 设备连接已关闭")


if __name__ == "__main__":
    flight_count = test_webview_extraction()
    print("\n" + "=" * 60)
    print(f"🎯 最终统计: 共识别到 {flight_count} 个航班")
    print("=" * 60)
