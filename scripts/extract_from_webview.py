#!/usr/bin/env python3
"""
WebView内容提取工具：尝试通过JavaScript和OCR两种方式提取航班信息
"""
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
    print("⚠️ OCR库未安装，将只使用JavaScript方式")


def extract_via_javascript(driver):
    """通过JavaScript从WebView中提取内容"""
    print("🔍 尝试通过JavaScript从WebView提取内容...")

    try:
        # 切换到WebView上下文
        contexts = driver.contexts
        webview_context = None

        for context in contexts:
            if 'WEBVIEW' in context.upper():
                webview_context = context
                break

        if not webview_context:
            print("⚠️ 未找到WebView上下文")
            return None

        print(f"📱 切换到WebView上下文: {webview_context}")
        driver.switch_to.context(webview_context)

        # 执行JavaScript获取页面文本内容
        script = """
        var allText = [];
        var elements = document.querySelectorAll('*');
        elements.forEach(function(el) {
            var text = el.innerText || el.textContent || '';
            if (text.trim()) {
                allText.push(text.trim());
            }
        });
        return allText.join('\\n');
        """

        page_text = driver.execute_script(script)
        print(f"✅ 通过JavaScript获取到 {len(page_text)} 字符的内容")

        # 切换回原生上下文
        driver.switch_to.context('NATIVE_APP')

        return page_text

    except Exception as e:
        print(f"⚠️ JavaScript提取失败: {e}")
        try:
            driver.switch_to.context('NATIVE_APP')
        except BaseException:
            pass
        return None


def extract_via_ocr(driver, screenshot_path=None):
    """通过OCR识别截图提取航班信息"""
    if not OCR_AVAILABLE:
        print("⚠️ OCR库未安装，跳过OCR识别")
        return None

    print("🔍 尝试通过OCR识别截图提取内容...")

    try:
        # 获取截图
        screenshot = driver.get_screenshot_as_png()

        # 保存截图（可选）
        if screenshot_path:
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            print(f"💾 截图已保存: {screenshot_path}")

        # 使用OCR识别
        image = Image.open(BytesIO(screenshot))
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')

        print(f"✅ OCR识别到 {len(text)} 字符的内容")
        return text

    except Exception as e:
        print(f"⚠️ OCR识别失败: {e}")
        return None


def extract_flights_from_text(text):
    """从文本中提取航班号"""
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


def extract_flights_hybrid(driver, output_dir=None):
    """
    混合方式提取航班信息：
    1. 先尝试JavaScript方式（适用于WebView）
    2. 如果失败，使用OCR识别截图
    """
    all_flights = set()

    # 方法1: JavaScript提取
    js_text = extract_via_javascript(driver)
    if js_text:
        js_flights = extract_flights_from_text(js_text)
        all_flights.update(js_flights)
        print(f"📊 JavaScript方式提取到 {len(js_flights)} 个航班: {sorted(js_flights)}")

    # 方法2: OCR识别
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            output_dir, f"ocr_screenshot_{timestamp}.png")
    else:
        screenshot_path = None

    ocr_text = extract_via_ocr(driver, screenshot_path)
    if ocr_text:
        ocr_flights = extract_flights_from_text(ocr_text)
        all_flights.update(ocr_flights)
        print(f"📊 OCR方式提取到 {len(ocr_flights)} 个航班: {sorted(ocr_flights)}")

    return all_flights, js_text, ocr_text


if __name__ == "__main__":
    driver = None
    try:
        print("=" * 60)
        print("🔌 连接设备...")
        print("=" * 60)
        driver = connect_device()
        print("✅ 设备连接成功\n")

        time.sleep(3)

        output_dir = os.path.join(os.path.dirname(__file__), "..", "results")
        os.makedirs(output_dir, exist_ok=True)

        print("=" * 60)
        print("🔍 使用混合方式提取航班信息...")
        print("=" * 60)

        flights, js_text, ocr_text = extract_flights_hybrid(driver, output_dir)

        print("\n" + "=" * 60)
        print("📊 提取结果")
        print("=" * 60)
        print(f"✅ 总共识别到 {len(flights)} 个航班")
        if flights:
            print(f"📋 航班号列表: {sorted(flights)}")

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(
            output_dir, f"webview_extraction_{timestamp}.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("WebView航班提取结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                f"提取时间: {
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"识别到的航班总数: {len(flights)}\n")
            if flights:
                f.write(f"航班号: {', '.join(sorted(flights))}\n")
            if js_text:
                f.write(f"\nJavaScript提取的文本长度: {len(js_text)} 字符\n")
            if ocr_text:
                f.write(f"OCR识别的文本长度: {len(ocr_text)} 字符\n")

        print(f"\n💾 结果已保存到: {result_file}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\n✅ 设备连接已关闭")
