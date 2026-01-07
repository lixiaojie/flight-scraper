#!/usr/bin/env python3
"""
调试脚本：获取当前页面的所有元素信息，帮助定位城市选择元素
"""

import sys
import os
from lxml import etree

try:
    from device_connection import connect_device
except Exception:
    sys.path.insert(0, os.path.dirname(__file__))
    from device_connection import connect_device


def debug_page_elements(driver):
    """调试页面元素"""
    print("🔍 获取页面源码...")
    page_source = driver.page_source

    print("📄 解析页面元素...")
    root = etree.fromstring(page_source.encode('utf-8'))

    # 获取所有有文本的元素
    print("\n" + "=" * 60)
    print("📋 页面中所有包含文本的元素:")
    print("=" * 60)

    elements_with_text = []
    for elem in root.xpath('//*[@text]'):
        text = elem.get('text', '').strip()
        if text:
            elem_info = {
                'text': text,
                'class': elem.tag,
                'clickable': elem.get('clickable', 'false'),
                'bounds': elem.get('bounds', ''),
                'resource_id': elem.get('resource-id', ''),
                'content_desc': elem.get('content-desc', '')
            }
            elements_with_text.append(elem_info)

    # 打印前50个元素
    for i, elem in enumerate(elements_with_text[:50], 1):
        print(f"\n{i}. 文本: {elem['text'][:50]}")
        print(f"   类名: {elem['class']}")
        print(f"   可点击: {elem['clickable']}")
        print(f"   资源ID: {elem['resource_id']}")
        print(f"   内容描述: {elem['content_desc']}")
        print(f"   位置: {elem['bounds']}")

    # 特别查找可能包含"出发"或"到达"的元素
    print("\n" + "=" * 60)
    print("🎯 包含'出发'或'到达'的元素:")
    print("=" * 60)

    city_keywords = ['出发', '到达', '城市', '北京', '上海', '选择']
    for keyword in city_keywords:
        matching = [e for e in elements_with_text if keyword in e['text']]
        if matching:
            print(f"\n包含'{keyword}'的元素 ({len(matching)}个):")
            for elem in matching[:10]:  # 只显示前10个
                print(
                    f"  - {elem['text'][:50]} (可点击: {elem['clickable']}, ID: {elem['resource_id']})")

    # 查找所有可点击的元素
    print("\n" + "=" * 60)
    print("👆 所有可点击的元素:")
    print("=" * 60)

    clickable_elements = [
        e for e in elements_with_text if e['clickable'] == 'true']
    for i, elem in enumerate(clickable_elements[:30], 1):
        print(f"{i}. {elem['text'][:50]} (ID: {elem['resource_id']})")

    # 保存页面源码到文件
    output_file = "/app/results/debug_page_source.xml"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"\n💾 页面源码已保存到: {output_file}")
    except Exception as e:
        print(f"⚠️ 保存页面源码失败: {e}")


if __name__ == "__main__":
    driver = None
    try:
        print("🔌 连接设备...")
        driver = connect_device()
        print("✅ 设备连接成功")

        print("\n⏳ 等待3秒，确保页面已加载...")
        import time
        time.sleep(3)

        debug_page_elements(driver)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

