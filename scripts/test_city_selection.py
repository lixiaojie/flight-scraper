#!/usr/bin/env python3
"""
独立的城市选择功能测试模块
测试空铁联运首页的城市选择功能：
1. 识别出发城市和到达城市的位置
2. 点击进入城市选择页面
3. 在搜索框输入城市名称首字母
4. 在搜索结果中选择城市
5. 返回上一页
"""

import time
import os
import sys
from datetime import datetime
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 导入设备连接模块
try:
    from device_connection import connect_device
    from page_capture import launch_12306_app, step2_check_homepage, step3_click_air_rail_transfer, step4_check_air_rail_page, wait_step
except Exception:
    # 兼容直接运行
    sys.path.insert(0, os.path.dirname(__file__))
    from device_connection import connect_device
    from page_capture import launch_12306_app, step2_check_homepage, step3_click_air_rail_transfer, step4_check_air_rail_page, wait_step


def get_city_pinyin_first_letter(city_name):
    """
    获取城市名称所有汉字的拼音首字母组合
    例如：北京->BJ，上海->SH，乌鲁木齐->WLMQ
    """
    # 完整的城市拼音首字母映射（每个汉字的首字母组合）
    city_pinyin_map = {
        # 一线城市
        '北京': 'BJ', '上海': 'SH', '广州': 'GZ', '深圳': 'SZ',
        # 新一线城市
        '成都': 'CD', '杭州': 'HZ', '南京': 'NJ', '武汉': 'WH',
        '西安': 'XA', '重庆': 'CQ', '天津': 'TJ', '苏州': 'SZ',
        '长沙': 'CS', '郑州': 'ZZ', '青岛': 'QD', '大连': 'DL',
        '厦门': 'XM', '福州': 'FZ', '济南': 'JN', '昆明': 'KM',
        '沈阳': 'SY', '哈尔滨': 'HEB', '石家庄': 'SJZ', '南昌': 'NC',
        '合肥': 'HF', '太原': 'TY', '长春': 'CC', '贵阳': 'GY',
        '乌鲁木齐': 'WLMQ', '兰州': 'LZ', '银川': 'YC', '西宁': 'XN',
        '呼和浩特': 'HHHT', '拉萨': 'LS', '海口': 'HK', '三亚': 'SY',
        # 其他常见城市
        '珠海': 'ZH', '中山': 'ZS', '东莞': 'DG', '佛山': 'FS',
        '无锡': 'WX', '常州': 'CZ', '南通': 'NT', '温州': 'WZ',
        '台州': 'TZ', '嘉兴': 'JX', '绍兴': 'SX', '金华': 'JH',
        '湖州': 'HZ', '舟山': 'ZS', '丽水': 'LS', '衢州': 'QZ',
        '宁波': 'NB', '扬州': 'YZ', '泰州': 'TZ', '镇江': 'ZJ',
        '盐城': 'YC', '淮安': 'HA', '宿迁': 'SQ', '连云港': 'LYG',
        '徐州': 'XZ', '宿州': 'SZ', '蚌埠': 'BB', '淮南': 'HN',
        '滁州': 'CZ', '六安': 'LA', '马鞍山': 'MAS', '芜湖': 'WH',
        '宣城': 'XC', '铜陵': 'TL', '池州': 'CZ', '安庆': 'AQ',
        '黄山': 'HS', '阜阳': 'FY', '亳州': 'BZ', '淮北': 'HB',
    }

    # 如果城市名在映射中，返回完整拼音首字母
    if city_name in city_pinyin_map:
        return city_pinyin_map[city_name]

    # 如果城市名包含"市"，去掉"市"再查找
    if city_name.endswith('市'):
        city_name_no_suffix = city_name[:-1]
        if city_name_no_suffix in city_pinyin_map:
            return city_pinyin_map[city_name_no_suffix]

    # 否则，尝试使用单字拼音首字母映射（组合每个汉字的首字母）
    char_pinyin = {
        '北': 'B', '京': 'J', '上': 'S', '海': 'H', '广': 'G', '州': 'Z',
        '深': 'S', '圳': 'Z', '成': 'C', '都': 'D', '杭': 'H', '南': 'N',
        '武': 'W', '汉': 'H', '西': 'X', '安': 'A', '重': 'C', '庆': 'Q',
        '天': 'T', '津': 'J', '苏': 'S', '长': 'C', '沙': 'S', '郑': 'Z',
        '青': 'Q', '岛': 'D', '大': 'D', '连': 'L', '厦': 'X', '门': 'M',
        '福': 'F', '济': 'J', '昆': 'K', '明': 'M', '沈': 'S', '阳': 'Y',
        '哈': 'H', '尔': 'E', '滨': 'B', '石': 'S', '家': 'J', '庄': 'Z',
        '合': 'H', '肥': 'F', '太': 'T', '原': 'Y', '春': 'C', '贵': 'G',
        '乌': 'W', '鲁': 'L', '木': 'M', '齐': 'Q', '兰': 'L', '银': 'Y',
        '川': 'C', '宁': 'N', '呼': 'H', '和': 'H', '浩': 'H', '特': 'T',
        '拉': 'L', '萨': 'S', '口': 'K', '三': 'S', '亚': 'Y',
    }

    # 尝试组合每个汉字的首字母
    if city_name:
        result = ''
        for char in city_name:
            if char in char_pinyin:
                result += char_pinyin[char]
            elif '\u4e00' <= char <= '\u9fff':
                result += char[0] if char else ''
        if result:
            return result

    # 最后的兜底方案：返回城市名本身
    return city_name if city_name else 'BJ'


def find_city_element(driver, city_type='出发', city_name=None):
    """
    查找出发城市或到达城市的元素

    Args:
        driver: WebDriver实例
        city_type: '出发' 或 '到达'
        city_name: 当前显示的城市名称（可选，用于精确定位）

    Returns:
        tuple: (WebElement or None, dict or None) - 元素和位置信息
    """
    print(f"🔍 查找{city_type}城市元素...")

    # 首先尝试从页面源码中查找城市元素及其位置
    try:
        page_source = driver.page_source
        from lxml import etree
        root = etree.fromstring(page_source.encode('utf-8'))

        # 查找所有包含城市名的TextView元素
        # 根据调试信息，城市元素是android.widget.TextView，位置在页面顶部区域
        city_elements = []

        # 如果提供了城市名，优先查找该城市
        if city_name:
            xpath_query = f'.//android.widget.TextView[@text="{city_name}"]'
            elements = root.xpath(xpath_query)
            for elem in elements:
                bounds = elem.get('bounds', '')
                # 解析bounds获取中心点坐标
                if bounds:
                    try:
                        # bounds格式: [x1,y1][x2,y2]
                        import re
                        match = re.search(
                            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            # 检查是否在合理的区域（城市选择通常在页面顶部，y坐标在500-800之间）
                            if 500 <= center_y <= 800:
                                city_elements.append({
                                    'text': city_name,
                                    'bounds': bounds,
                                    'center': (center_x, center_y),
                                    'element': elem
                                })
                                print(
                                    f"✅ 找到城市元素: {city_name}, 位置: {bounds}, 中心: ({center_x}, {center_y})")
                    except BaseException:
                        pass

        # 如果没有找到或未提供城市名，尝试查找所有可能的城市元素
        if not city_elements:
            # 查找所有TextView，过滤出可能是城市的元素
            all_textviews = root.xpath('.//android.widget.TextView[@text]')
            for elem in all_textviews:
                text = elem.get('text', '').strip()
                bounds = elem.get('bounds', '')
                # 城市名通常是2-4个中文字符，且在特定位置
                if text and 2 <= len(text) <= 4 and all(
                        '\u4e00' <= c <= '\u9fff' for c in text):
                    try:
                        match = re.search(
                            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            # 检查是否在城市选择区域（根据调试信息，y坐标在550-760之间）
                            if 500 <= center_y <= 800 and 50 <= center_x <= 1000:
                                city_elements.append({
                                    'text': text,
                                    'bounds': bounds,
                                    'center': (center_x, center_y),
                                    'element': elem
                                })
                    except BaseException:
                        pass

        # 根据city_type选择对应的城市元素
        # 根据调试信息：北京在左侧(91-472)，上海在右侧(611-992)
        if city_elements:
            if city_type == '出发':
                # 出发城市通常在左侧
                city_info = min(city_elements, key=lambda x: x['center'][0])
            else:  # 到达
                # 到达城市通常在右侧
                city_info = max(city_elements, key=lambda x: x['center'][0])

            print(
                f"✅ 找到{city_type}城市元素: {
                    city_info['text']}, 位置: {
                    city_info['bounds']}")

            # 尝试通过文本定位元素
            try:
                element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{
                        city_info["text"]}")')
                return element, city_info
            except BaseException:
                # 如果无法通过文本定位，返回位置信息用于坐标点击
                print(f"⚠️ 无法通过文本定位元素，将使用坐标点击: {city_info['center']}")
                return None, city_info

    except Exception as e:
        print(f"⚠️ 从页面源码查找失败: {e}")

    # 备用方案：尝试通过UiSelector查找
    try:
        # 尝试查找包含城市名的元素（不限制可点击）
        elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.TextView")')
        for element in elements:
            try:
                text = element.text
                if text and 2 <= len(text) <= 4 and all(
                        '\u4e00' <= c <= '\u9fff' for c in text):
                    location = element.location
                    size = element.size
                    center_y = location['y'] + size['height'] // 2
                    # 检查是否在城市选择区域
                    if 500 <= center_y <= 800:
                        print(f"✅ 通过UiSelector找到城市元素: {text}")
                        return element, None
            except BaseException:
                continue
    except Exception as e:
        print(f"⚠️ 通过UiSelector查找失败: {e}")

    print(f"❌ 未找到{city_type}城市元素")
    return None, None


def click_city_and_enter_selection(driver, city_type='出发', current_city=None):
    """
    点击城市元素，进入城市选择页面

    Args:
        driver: WebDriver实例
        city_type: '出发' 或 '到达'
        current_city: 当前显示的城市名称（可选）

    Returns:
        bool: 是否成功进入城市选择页面
    """
    print(f"\n📍 步骤: 点击{city_type}城市，进入城市选择页面")

    # 查找城市元素
    city_element, city_info = find_city_element(
        driver, city_type, current_city)

    try:
        # 如果找到了元素，尝试点击
        if city_element:
            try:
                city_element.click()
                print(f"✅ 已点击{city_type}城市元素")
            except Exception as e:
                print(f"⚠️ 点击元素失败: {e}，尝试坐标点击")
                # 如果元素点击失败，尝试坐标点击
                if city_info and 'center' in city_info:
                    center_x, center_y = city_info['center']
                    driver.tap([(center_x, center_y)], 100)
                    print(f"✅ 已通过坐标点击{city_type}城市: ({center_x}, {center_y})")
                else:
                    raise
        elif city_info and 'center' in city_info:
            # 如果只找到了位置信息，使用坐标点击
            center_x, center_y = city_info['center']
            driver.tap([(center_x, center_y)], 100)
            print(f"✅ 已通过坐标点击{city_type}城市: ({center_x}, {center_y})")
        else:
            print(f"❌ 未找到{city_type}城市元素或位置信息")
            return False

        import time
        time.sleep(2)

        # 检查是否进入城市选择页面
        # 通常城市选择页面会有搜索框
        try:
            # 等待搜索框出现（通常包含"搜索"或"请输入"等文本）
            search_indicators = ['搜索', '请输入', '城市', 'Search']
            found = False
            for indicator in search_indicators:
                try:
                    search_element = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{indicator}")')
                    if search_element:
                        print(f"✅ 已进入城市选择页面（找到搜索指示器: {indicator}）")
                        found = True
                        break
                except BaseException:
                    continue

            if not found:
                # 尝试查找EditText元素（搜索框通常是EditText）
                try:
                    edit_texts = driver.find_elements(
                        AppiumBy.CLASS_NAME, "android.widget.EditText")
                    if edit_texts:
                        print(f"✅ 已进入城市选择页面（找到 {len(edit_texts)} 个EditText元素）")
                        found = True
                except BaseException:
                    pass

            if not found:
                print("⚠️ 未明确检测到城市选择页面，但继续执行...")

            return True

        except Exception as e:
            print(f"⚠️ 检查城市选择页面时出错: {e}")
            return True  # 即使检查失败，也继续执行

    except Exception as e:
        print(f"❌ 点击{city_type}城市失败: {e}")
        return False


def find_search_box(driver):
    """
    查找城市选择页面的搜索框

    Returns:
        WebElement or None: 搜索框元素
    """
    print("🔍 查找搜索框...")

    # 方式1: 查找EditText元素
    try:
        edit_texts = driver.find_elements(
            AppiumBy.CLASS_NAME, "android.widget.EditText")
        if edit_texts:
            # 通常第一个EditText是搜索框
            search_box = edit_texts[0]
            print("✅ 找到搜索框（EditText）")
            return search_box
    except Exception as e:
        print(f"⚠️ 查找EditText失败: {e}")

    # 方式2: 通过文本查找包含"搜索"或"请输入"的元素
    try:
        for text in ['搜索', '请输入', 'Search', '城市']:
            try:
                element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{text}")')
                # 检查是否是输入框
                if element.tag_name == 'android.widget.EditText' or 'EditText' in str(
                        element):
                    print(f"✅ 找到搜索框（通过文本: {text}）")
                    return element
            except BaseException:
                continue
    except Exception as e:
        print(f"⚠️ 通过文本查找搜索框失败: {e}")

    # 方式3: 通过资源ID查找（如果知道具体的ID）
    try:
        search_ids = [
            "com.MobileTicket:id/search",
            "com.MobileTicket:id/city_search",
            "com.MobileTicket:id/search_input"
        ]
        for search_id in search_ids:
            try:
                element = driver.find_element(AppiumBy.ID, search_id)
                print(f"✅ 找到搜索框（通过ID: {search_id}）")
                return element
            except BaseException:
                continue
    except Exception as e:
        print(f"⚠️ 通过ID查找搜索框失败: {e}")

    print("❌ 未找到搜索框")
    return None


def input_city_search(driver, city_name):
    """
    在搜索框中输入城市名称的拼音首字母（每个汉字的首字母组合）

    Args:
        driver: WebDriver实例
        city_name: 城市名称（中文）

    Returns:
        bool: 是否成功输入
    """
    print(f"\n⌨️ 步骤: 在搜索框输入城市 '{city_name}' 的拼音首字母")

    # 获取城市拼音首字母（每个汉字的首字母组合）
    pinyin_initials = get_city_pinyin_first_letter(city_name)
    print(f"📝 城市 '{city_name}' 的拼音首字母: {pinyin_initials}")

    # 查找搜索框
    search_box = find_search_box(driver)
    if not search_box:
        print("❌ 未找到搜索框")
        return False

    try:
        # 清空搜索框（如果有内容）
        try:
            search_box.clear()
        except BaseException:
            pass

        # 输入拼音首字母
        search_box.send_keys(pinyin_initials)
        print(f"✅ 已输入拼音首字母: {pinyin_initials}")
        wait_step(driver, 2)  # 等待搜索结果加载

        return True

    except Exception as e:
        print(f"❌ 输入搜索内容失败: {e}")
        return False


def select_city_from_results(driver, city_name):
    """
    从搜索结果中选择目标城市

    Args:
        driver: WebDriver实例
        city_name: 目标城市名称

    Returns:
        bool: 是否成功选择城市
    """
    print(f"\n🎯 步骤: 从搜索结果中选择城市 '{city_name}'")

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            # 方式1: 直接通过城市名称查找
            try:
                city_element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{city_name}")')
                city_element.click()
                print(f"✅ 成功选择城市: {city_name}")
                wait_step(driver, 2)
                return True
            except NoSuchElementException:
                pass

            # 方式2: 通过包含城市名称的文本查找
            try:
                city_element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{city_name}")')
                city_element.click()
                print(f"✅ 成功选择城市（通过textContains）: {city_name}")
                wait_step(driver, 2)
                return True
            except NoSuchElementException:
                pass

            # 方式3: 从页面源码中查找
            try:
                page_source = driver.page_source
                from lxml import etree
                root = etree.fromstring(page_source.encode('utf-8'))

                # 查找包含城市名称的元素
                xpath_query = f'.//*[contains(@text, "{city_name}")]'
                elements = root.xpath(xpath_query)

                for elem in elements:
                    text = elem.get('text', '')
                    if city_name in text:
                        try:
                            city_element = driver.find_element(
                                AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")')
                            city_element.click()
                            print(f"✅ 成功选择城市（通过页面源码）: {text}")
                            wait_step(driver, 2)
                            return True
                        except BaseException:
                            continue
            except Exception as e:
                print(f"⚠️ 从页面源码查找城市失败: {e}")

            # 如果当前页面没有找到，尝试向下滚动
            if attempt < max_attempts:
                print(f"⚠️ 第{attempt}次尝试未找到城市，尝试滚动...")
                try:
                    # 向下滚动
                    screen_size = driver.get_window_size()
                    driver.swipe(screen_size['width'] // 2,
                                 screen_size['height'] * 0.7,
                                 screen_size['width'] // 2,
                                 screen_size['height'] * 0.3,
                                 500)
                    wait_step(driver, 1)
                except BaseException:
                    pass
            else:
                print(f"❌ 尝试{max_attempts}次后仍未找到城市: {city_name}")
                return False

        except Exception as e:
            print(f"❌ 选择城市时出错: {e}")
            if attempt >= max_attempts:
                return False
            wait_step(driver, 1)

    return False


def go_back_to_previous_page(driver):
    """
    返回上一页

    Args:
        driver: WebDriver实例

    Returns:
        bool: 是否成功返回
    """
    print("\n🔙 步骤: 返回上一页")

    try:
        # 方式1: 使用返回键
        driver.back()
        print("✅ 已按返回键")
        wait_step(driver, 2)
        return True
    except Exception as e:
        print(f"⚠️ 按返回键失败: {e}")

        # 方式2: 查找返回按钮
        try:
            back_buttons = ['返回', 'Back', '←', '取消']
            for btn_text in back_buttons:
                try:
                    back_btn = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().text("{btn_text}")')
                    back_btn.click()
                    print(f"✅ 已点击返回按钮: {btn_text}")
                    wait_step(driver, 2)
                    return True
                except BaseException:
                    continue
        except Exception as e2:
            print(f"⚠️ 查找返回按钮失败: {e2}")

        return False


def test_city_selection(driver, from_city='北京', to_city='上海'):
    """
    完整的城市选择测试流程

    Args:
        driver: WebDriver实例
        from_city: 出发城市名称
        to_city: 到达城市名称

    Returns:
        bool: 测试是否成功
    """
    print("\n" + "=" * 60)
    print("🧪 开始城市选择功能测试")
    print("=" * 60)

    success = True

    # 测试出发城市选择
    print(f"\n📍 测试1: 选择出发城市 '{from_city}'")
    # 先获取当前显示的出发城市（可能是from_city或其他）
    if not click_city_and_enter_selection(driver, '出发', from_city):
        print("❌ 测试1失败: 无法进入城市选择页面")
        success = False
    else:
        if not input_city_search(driver, from_city):
            print("❌ 测试1失败: 无法输入搜索内容")
            success = False
        else:
            if not select_city_from_results(driver, from_city):
                print("❌ 测试1失败: 无法选择城市")
                success = False
            else:
                # 选择城市后，APP会自动返回空铁联运页面，无需手动返回
                print("✅ 测试1完成: 出发城市选择成功")
                wait_step(driver, 2)  # 等待页面加载

    wait_step(driver, 2)

    # 测试到达城市选择
    print(f"\n📍 测试2: 选择到达城市 '{to_city}'")
    if not click_city_and_enter_selection(driver, '到达', to_city):
        print("❌ 测试2失败: 无法进入城市选择页面")
        success = False
    else:
        if not input_city_search(driver, to_city):
            print("❌ 测试2失败: 无法输入搜索内容")
            success = False
        else:
            if not select_city_from_results(driver, to_city):
                print("❌ 测试2失败: 无法选择城市")
                success = False
            else:
                # 选择城市后，APP会自动返回空铁联运页面，无需手动返回
                print("✅ 测试2完成: 到达城市选择成功")
                wait_step(driver, 2)  # 等待页面加载

    print("\n" + "=" * 60)
    if success:
        print("✅ 城市选择功能测试完成！")
        print("📱 设备将停留在空铁联运首页，请手动检查结果")
    else:
        print("❌ 城市选择功能测试部分失败，请检查日志")
    print("=" * 60)

    return success


def main():
    """主函数"""
    driver = None

    try:
        # 连接设备
        print("🔌 连接设备...")
        driver = connect_device()

        # 启动12306应用
        if not launch_12306_app(driver):
            print("❌ 无法启动12306应用")
            return False

        # 检查主页面
        if not step2_check_homepage(driver):
            print("❌ 无法进入主页面")
            return False

        # 点击空铁联运
        if not step3_click_air_rail_transfer(driver):
            print("❌ 无法进入空铁联运页面")
            return False

        # 检查空铁联运首页（如果失败，仍然尝试继续，因为页面可能已经加载）
        air_rail_found = step4_check_air_rail_page(driver)
        if not air_rail_found:
            print("⚠️ 未明确找到空铁联运首页标识，但继续尝试执行城市选择测试...")
            print("💡 提示: 如果页面已加载，城市选择功能仍可能正常工作")
        else:
            print("✅ 已确认进入空铁联运首页")

        print("✅ 开始测试城市选择功能")
        wait_step(driver, 3)  # 增加等待时间，确保页面完全加载

        # 从环境变量获取测试城市，如果没有则使用默认值
        from_city = os.getenv("TEST_FROM_CITY", "北京")
        to_city = os.getenv("TEST_TO_CITY", "上海")

        print(f"📋 测试配置: 出发城市={from_city}, 到达城市={to_city}")

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
        # 如果需要关闭，可以取消下面的注释
        # if driver:
        #     driver.quit()
        #     print("🔚 驱动已关闭")
        pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
