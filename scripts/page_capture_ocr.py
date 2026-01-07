#!/usr/bin/env python3
"""
OCR增强的页面抓取模块：使用OCR识别截图提取航班信息
适用于H5/WebView页面，可以识别所有可见内容
"""
import time
import os
import re
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from page_capture import (
    scroll_to_top,
    swipe_down_in_middle,
    find_scrollable_list,
    extract_flight_elements_from_xml
)


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


def extract_flights_from_screenshot(driver, use_ocr=True):
    """从截图中提取航班信息（OCR或XML）"""
    if use_ocr and OCR_AVAILABLE:
        try:
            # 获取截图
            screenshot = driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))

            # 使用OCR识别（中英文混合）
            # 添加更多OCR配置以提高识别准确率
            custom_config = r'--oem 3 --psm 6'  # PSM 6: 假设统一的文本块
            text = pytesseract.image_to_string(image, lang='chi_sim+eng', config=custom_config)

            # 提取航班号
            flights = extract_flights_from_ocr_text(text)
            if flights:
                print(f"📸 OCR识别到 {len(flights)} 个航班: {sorted(flights)}")
            return flights, text
        except Exception as e:
            print(f"⚠️ OCR识别失败: {e}，回退到XML提取")

    # 回退到XML提取
    try:
        page_source = driver.page_source
        flights, _, _ = extract_flight_elements_from_xml(
            page_source, driver=None)
        return flights, None
    except Exception as e:
        print(f"⚠️ XML提取也失败: {e}")
        return set(), None


def smart_scroll_and_capture_ocr(
        driver,
        output_dir,
        use_ocr=True,
        max_scrolls=30,  # 增加最大滚动次数，确保能加载所有内容
        min_scrolls=5):  # 增加最小滚动次数
    """
    使用OCR的智能滚动和抓取策略

    优化策略：
    1. 使用OCR识别截图，适用于H5/WebView页面
    2. 智能检测新内容，避免重复识别
    3. 连续无新内容时提前停止
    4. 收集OCR文本用于完整信息提取
    5. 可选的截图保存（用于调试）

    Args:
        driver: WebDriver实例
        output_dir: 输出目录
        use_ocr: 是否使用OCR（默认True）
        max_scrolls: 最大滚动次数（默认20，优化后）
        min_scrolls: 最小滚动次数，确保至少滚动多次（默认3）

    Returns:
        tuple: (all_flights_set, all_ocr_text, screenshot_paths_list)
    """
    if use_ocr and not OCR_AVAILABLE:
        print("⚠️ OCR库未安装，回退到XML提取模式")
        use_ocr = False

    print("🔄 开始OCR智能滚动以加载所有航班信息...")

    # 等待页面完全加载（优化：减少等待时间）
    time.sleep(1.5)

    # 查找可滚动元素
    scrollable_info = find_scrollable_list(driver)

    # 滚动到顶部
    print("📍 滚动到页面顶部...")
    scroll_to_top(driver)
    time.sleep(1.0)  # 优化：减少等待时间

    # 存储所有航班、OCR文本和截图路径
    all_flights = set()
    all_ocr_text = []  # 收集所有OCR文本，用于完整信息提取
    screenshot_paths = []
    scroll_count = 0
    no_new_content_count = 0
    max_no_new_content = 5  # 连续5次无新内容则停止（增加容错）

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🔄 开始滚动并提取航班信息...")

    while scroll_count < max_scrolls:
        scroll_count += 1
        print(f"\n🔄 第{scroll_count}次滚动和识别...")

        # 提取航班信息
        flights, ocr_text = extract_flights_from_screenshot(
            driver, use_ocr=use_ocr)

        # 收集OCR文本（用于后续完整信息提取）
        if ocr_text:
            all_ocr_text.append(ocr_text)

        # 检查是否有新航班
        new_flights = flights - all_flights
        if new_flights:
            all_flights.update(flights)
            no_new_content_count = 0
            print(f"✅ 识别到 {len(flights)} 个航班，新增 {len(new_flights)} 个: {sorted(new_flights)}")
        else:
            no_new_content_count += 1
            print(f"📊 识别到 {len(flights)} 个航班，无新增（连续{no_new_content_count}次）")

        # 保存截图（可选，用于调试）- 优化：只保存前5张
        if output_dir and scroll_count <= 5:  # 只保存前5张截图以节省空间和时间
            screenshot_path = os.path.join(output_dir, f"ocr_scroll_{timestamp}_{scroll_count:02d}.png")
            try:
                driver.save_screenshot(screenshot_path)
                screenshot_paths.append(screenshot_path)
            except Exception as e:
                print(f"⚠️ 保存截图失败: {e}")

        # 如果连续多次无新内容，且已超过最小滚动次数，停止滚动
        if no_new_content_count >= max_no_new_content and scroll_count >= min_scrolls:
            print(f"⚠️ 连续{max_no_new_content}次未发现新航班，停止滚动")
            break

        # 向下滚动 - 使用多种滚动方式确保内容加载
        if scroll_count < max_scrolls:
            # 尝试多种滚动方式，增加滚动距离
            try:
                # 方式1: 使用 swipe_down_in_middle
                swipe_down_in_middle(driver, scrollable_info)
            except Exception as e:
                print(f"⚠️ swipe_down_in_middle 失败: {e}，尝试备用方式")
                try:
                    # 方式2: 使用更大的滚动距离
                    size = driver.get_window_size()
                    start_y = int(size['height'] * 0.7)  # 从70%开始
                    end_y = int(size['height'] * 0.3)     # 滚动到30%（更大的滚动距离）
                    center_x = int(size['width'] * 0.5)
                    print(f"📍 使用备用滚动方式: 从 Y={start_y} 到 Y={end_y}")
                    driver.swipe(center_x, start_y, center_x, end_y, 600)  # 增加持续时间
                except Exception as e2:
                    print(f"⚠️ 备用滚动方式也失败: {e2}")
                    # 方式3: 尝试多次小幅滚动
                    try:
                        size = driver.get_window_size()
                        center_x = int(size['width'] * 0.5)
                        for i in range(2):  # 连续滚动2次
                            start_y = int(size['height'] * (0.65 - i * 0.1))
                            end_y = int(size['height'] * (0.35 - i * 0.1))
                            driver.swipe(center_x, start_y, center_x, end_y, 400)
                            time.sleep(0.3)
                    except Exception as e3:
                        print(f"⚠️ 多次滚动方式也失败: {e3}")
            
            # 根据是否有新内容动态调整等待时间
            # 如果有新内容，说明页面加载快，可以缩短等待时间
            # 如果无新内容，可能是页面加载慢，需要增加等待时间
            if new_flights:
                wait_time = 2.0  # 有新内容时，等待2秒
            else:
                wait_time = 2.5  # 无新内容时，等待2.5秒，确保页面完全加载
            time.sleep(wait_time)

    # 合并所有OCR文本
    combined_ocr_text = '\n'.join(all_ocr_text) if all_ocr_text else None

    print(f"\n🏁 滚动完成，总共滚动 {scroll_count} 次，识别到 {len(all_flights)} 个唯一航班")

    # 保存最终结果摘要
    if output_dir:
        summary_file = os.path.join(output_dir,
                                    f"ocr_extraction_summary_{timestamp}.txt")
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("OCR航班提取摘要\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"滚动次数: {scroll_count}\n")
                f.write(f"识别到的航班总数: {len(all_flights)}\n\n")
                if all_flights:
                    f.write(f"航班号列表:\n")
                    for flight in sorted(all_flights):
                        f.write(f"  - {flight}\n")
            print(f"💾 提取摘要已保存: {summary_file}")
        except Exception as e:
            print(f"⚠️ 保存摘要失败: {e}")

    return all_flights, combined_ocr_text, screenshot_paths


def smart_scroll_and_capture_hybrid(driver, output_dir, prefer_ocr=True):
    """
    混合模式：先尝试OCR，如果失败则回退到XML提取

    Args:
        driver: WebDriver实例
        output_dir: 输出目录
        prefer_ocr: 是否优先使用OCR（默认True）

    Returns:
        tuple: (all_flights_set, ocr_text, method_used)
    """
    if prefer_ocr and OCR_AVAILABLE:
        try:
            print("🔍 尝试使用OCR模式...")
            flights, ocr_text, _ = smart_scroll_and_capture_ocr(
                driver, output_dir, use_ocr=True)
            return flights, ocr_text, 'ocr'
        except Exception as e:
            print(f"⚠️ OCR模式失败: {e}，回退到XML模式")

    # 回退到XML模式
    print("🔍 使用XML提取模式...")
    from page_capture import smart_scroll_and_capture
    page_source, _ = smart_scroll_and_capture(driver, output_dir)
    flights, _, _ = extract_flight_elements_from_xml(page_source, driver=None)
    return flights, None, 'xml'
