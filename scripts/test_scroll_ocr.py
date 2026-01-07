#!/usr/bin/env python3
"""
测试滚动截图OCR识别方法
用于测试和改进结果页的滚动和识别逻辑
"""
import os
import sys
import time
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入，支持相对导入和绝对导入
try:
    from .device_connection import connect_device
    from .page_capture_ocr import smart_scroll_and_capture_ocr, extract_flights_from_screenshot
except ImportError:
    try:
        from device_connection import connect_device
        from page_capture_ocr import smart_scroll_and_capture_ocr, extract_flights_from_screenshot
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 提示: 请在 Docker 容器内运行此脚本，或确保已安装所有依赖")
        sys.exit(1)

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR库未安装，将使用XML提取模式")

def test_scroll_ocr():
    """测试滚动OCR识别"""
    print("=" * 80)
    print("测试滚动截图OCR识别方法")
    print("=" * 80)
    
    # 连接设备
    print("\n🔌 连接设备...")
    driver = connect_device()
    if not driver:
        print("❌ 设备连接失败")
        return
    
    try:
        # 等待用户确认设备已停留在结果页
        print("\n⏳ 等待5秒，请确保设备已停留在结果页...")
        time.sleep(5)
        
        # 输出目录
        output_dir = os.path.join(os.getcwd(), "results")
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n🔄 开始测试OCR滚动识别...")
        print("=" * 80)
        
        # 测试1: 单次截图识别
        print("\n📸 测试1: 单次截图识别")
        flights1, ocr_text1 = extract_flights_from_screenshot(driver, use_ocr=True)
        print(f"✅ 识别到 {len(flights1)} 个航班: {sorted(flights1)}")
        if ocr_text1:
            print(f"📝 OCR文本长度: {len(ocr_text1)} 字符")
            # 保存OCR文本
            ocr_file = os.path.join(output_dir, f"test_ocr_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(ocr_file, 'w', encoding='utf-8') as f:
                f.write(ocr_text1)
            print(f"💾 OCR文本已保存: {ocr_file}")
        
        # 测试2: 滚动识别
        print("\n🔄 测试2: 滚动识别（最多30次）")
        all_flights, all_ocr_text, screenshot_paths = smart_scroll_and_capture_ocr(
            driver, output_dir, use_ocr=True, max_scrolls=30, min_scrolls=5
        )
        
        print("\n" + "=" * 80)
        print("测试结果")
        print("=" * 80)
        print(f"✅ 总共识别到 {len(all_flights)} 个唯一航班")
        print(f"📸 保存了 {len(screenshot_paths)} 张截图")
        print(f"📝 收集了 {len(all_ocr_text)} 段OCR文本")
        
        if all_flights:
            print(f"\n📋 航班列表:")
            for i, flight in enumerate(sorted(all_flights), 1):
                print(f"  {i}. {flight}")
        
        # 保存完整OCR文本
        if all_ocr_text:
            combined_text = '\n'.join(all_ocr_text)
            combined_file = os.path.join(output_dir, f"test_combined_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(combined_file, 'w', encoding='utf-8') as f:
                f.write(combined_text)
            print(f"\n💾 完整OCR文本已保存: {combined_file}")
            print(f"📝 总文本长度: {len(combined_text)} 字符")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 80)
        print("测试完成，设备保持连接状态")
        print("=" * 80)
        # 不关闭驱动，让用户可以继续测试
        # driver.quit()

if __name__ == "__main__":
    test_scroll_ocr()

