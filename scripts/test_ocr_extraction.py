#!/usr/bin/env python3
"""
使用OCR识别截图提取航班信息（适用于WebView页面）
"""
from page_capture import scroll_to_top, swipe_down_in_middle, find_scrollable_list
from device_connection import connect_device
import sys
import os
import time
import re
from datetime import datetime
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR库未安装，请安装: pip install Pillow pytesseract")
    print("   并确保系统已安装tesseract: https://github.com/tesseract-ocr/tesseract")


def extract_flights_from_ocr_text(text):
    """从OCR识别的文本中提取航班号"""
    if not text:
        return set()

    # 提取航班号（2-4个大写字母 + 3-5个数字）
    flight_pattern = r'[A-Z]{2,4}\d{3,5}'
    flights = re.findall(flight_pattern, text)

    # 验证航班号格式
    valid_flights = set()
    for flight in flights:
        if len(flight) >= 5 and re.match(r'^[A-Z]{2,4}\d{3,5}$', flight):
            valid_flights.add(flight)

    return valid_flights


def extract_flights_from_screenshot(driver, screenshot_path=None):
    """从截图中使用OCR提取航班信息"""
    if not OCR_AVAILABLE:
        print("⚠️ OCR库未安装")
        return set(), None

    try:
        # 获取截图
        screenshot = driver.get_screenshot_as_png()

        # 保存截图
        if screenshot_path:
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            print(f"💾 截图已保存: {screenshot_path}")

        # 使用OCR识别
        image = Image.open(BytesIO(screenshot))
        # 使用中英文混合识别
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')

        # 提取航班号
        flights = extract_flights_from_ocr_text(text)

        return flights, text

    except Exception as e:
        print(f"⚠️ OCR识别失败: {e}")
        return set(), None


def test_ocr_extraction():
    """测试OCR提取"""
    driver = None

    try:
        print("=" * 60)
        print("🔌 连接设备...")
        print("=" * 60)
        driver = connect_device()
        print("✅ 设备连接成功\n")

        if not OCR_AVAILABLE:
            print("❌ OCR库未安装，无法继续")
            return 0

        time.sleep(3)

        output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 滚动到顶部
        print("📍 滚动到页面顶部...")
        scroll_to_top(driver)
        time.sleep(2)

        all_flights = set()
        scroll_count = 0
        max_scrolls = 20
        scrollable_info = find_scrollable_list(driver)

        print("\n" + "=" * 60)
        print("🔄 开始滚动并OCR识别...")
        print("=" * 60)

        while scroll_count < max_scrolls:
            scroll_count += 1
            print(f"\n🔄 第{scroll_count}次滚动和OCR识别...")

            # 获取截图并OCR识别
            screenshot_path = os.path.join(
                output_dir, f"ocr_screenshot_{timestamp}_{
                    scroll_count:02d}.png")
            flights, ocr_text = extract_flights_from_screenshot(
                driver, screenshot_path)

            if flights:
                new_flights = flights - all_flights
                all_flights.update(flights)
                print(f"📊 本次识别到 {len(flights)} 个航班，新增 {len(new_flights)} 个")
                if new_flights:
                    print(f"✅ 新增航班: {sorted(new_flights)}")
                else:
                    print("⚠️ 未发现新航班")
            else:
                print("⚠️ 本次未识别到航班")

            # 向下滚动
            print("📍 向下滚动...")
            swipe_down_in_middle(driver, scrollable_info)
            time.sleep(3)  # 等待内容加载

            # 如果连续3次没有新航班，停止滚动
            if scroll_count >= 3 and len(new_flights) == 0:
                print("⚠️ 连续未发现新航班，停止滚动")
                break

        print("\n" + "=" * 60)
        print("📊 最终结果")
        print("=" * 60)
        print(f"✅ 总共识别到 {len(all_flights)} 个航班")
        if all_flights:
            print(f"📋 航班号列表: {sorted(all_flights)}")

        # 保存结果
        result_file = os.path.join(
            output_dir, f"ocr_extraction_{timestamp}.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("OCR航班提取结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                f"提取时间: {
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"识别到的航班总数: {len(all_flights)}\n")
            if all_flights:
                f.write(f"航班号: {', '.join(sorted(all_flights))}\n")

        print(f"\n💾 结果已保存到: {result_file}")

        return len(all_flights)

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
    flight_count = test_ocr_extraction()
    print("\n" + "=" * 60)
    print(f"🎯 最终统计: 共识别到 {flight_count} 个航班")
    print("=" * 60)
