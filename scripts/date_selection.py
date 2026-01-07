# -*- coding: utf-8 -*-
# 此文件由 page_capture.py 分拆而来

import time
import os
import re
from datetime import datetime, date, timedelta
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from lxml import etree
from io import StringIO
from utils import tprint, wait_step, parse_bounds

def step4c_select_date(driver, depart_date):
    """步骤4C: 选择出发日期（根据页面展示文案拼装并点击）"""
    print("\n📅 步骤4C: 选择出发日期（按展示文案匹配）")
    
    if not depart_date:
        print("ℹ️ 未提供出发日期，跳过选择")
        return True
    
    # 先检查当前页面显示的日期是否与目标一致
    try:
        from city_selection import get_current_page_settings
        current_settings = get_current_page_settings(driver)
        current_date = current_settings.get('depart_date')
        
        if current_date:
            # 尝试解析当前日期和目标日期进行比较
            try:
                target_date_obj = datetime.strptime(depart_date, "%Y-%m-%d").date()
                current_date_obj = datetime.strptime(current_date, "%Y-%m-%d").date()
                if current_date_obj == target_date_obj:
                    print(f"✅ 当前日期已是 {depart_date}，无需修改")
                    return True
            except:
                # 如果日期格式不匹配，继续执行选择流程
                pass
    except Exception as e:
        print(f"⚠️ 检查当前日期失败: {e}，继续执行日期选择")
        
    try:
        today = date.today()
        weekday_map = {
            0: "周一",
            1: "周二",
            2: "周三",
            3: "周四",
            4: "周五",
            5: "周六",
            6: "周日"}

        # 查找任何形如"X月X日周X"格式的日期文本并点击激活日历视图
        calendar_opened = False
        print("🔄 尝试打开日历...")
        try:
            # 尝试点击任何包含"月"和"日"的按钮（包括历史日期）
            page = driver.page_source
            date_candidates = []
            try:
                root = etree.fromstring(page.encode('utf-8'))
                for el in root.xpath('//*[@text]'):
                    text = el.get('text') or ''
                    # 匹配形如"10月27日周一"这样的日期格式
                    if ('月' in text and '日' in text and (
                            '周' in text or '今天' in text or '明天' in text or '后天' in text)):
                        date_candidates.append(text)
                        
                print(f"🔍 找到的日期候选: {date_candidates}")
                
                # 尝试点击第一个找到的日期按钮
                for text in date_candidates:
                    try:
                        btn = driver.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().text("{text}")')
                        btn.click()
                        print(f"✅ 已点击日期按钮: {text}")
                        wait_step(driver, 1)
                        calendar_opened = True
                        break
                    except Exception as e:

                        print(f"⚠️ 点击日期按钮失败: {text}, {e}")
                        continue
                        
            except Exception as e:


                print(f"⚠️ 解析页面失败: {e}")
        except Exception as e:


            print(f"⚠️ 打开日历失败: {e}")
        
        # 如果成功打开了日历，等待日历加载
        if calendar_opened:
            print("⏳ 等待日历完全加载...")
            wait_step(driver, 2)  # 等待日历加载
            print("✅ 日历已加载完成")

        try:
            target = datetime.strptime(depart_date, "%Y-%m-%d").date()
        except Exception:

            print(f"⚠️ 出发日期格式非法: {depart_date}")
            return True

        # 生成候选展示文案
        month_day = f"{target.month}月{target.day}日"
        delta = (target - today).days
        candidates = []
        if delta == 0:
            candidates.append(f"{month_day}今天")
        elif delta == 1:

            candidates.append(f"{month_day}明天")
        elif delta == 2:

            candidates.append(f"{month_day}后天")
        # 周几文案始终作为候选
        candidates.append(f"{month_day}{weekday_map[target.weekday()]}")

        # 提取页面文本（如果日历已打开，使用刷新后的页面源码）
        if not calendar_opened:
            page = driver.page_source
        
        visible_texts = set()
        try:
            root = etree.fromstring(page.encode('utf-8'))
            for el in root.xpath('//*[@text]'):
                t = el.get('text') or ''
                if t:
                    visible_texts.add(t)
        except Exception:

            pass

        # 调试：打印所有可见的日期相关文本
        date_related_texts = [
            t for t in visible_texts if '月' in t and '日' in t]
        print(f"🔍 页面中找到的日期相关文本: {date_related_texts}")
        print(f"🎯 目标候选文案: {candidates}")
        
        # 如果日历已打开，也显示所有可见文本以便调试
        if calendar_opened:
            all_texts = [t for t in visible_texts if t.strip()]
            print(f"🔍 日历视图中的所有文本: {all_texts[:20]}...")  # 只显示前20个避免日志过长
            
            # 特别查找目标日期的数字
            target_day_str = str(target.day)
            day_texts = [t for t in all_texts if target_day_str in t]
            print(f"🎯 包含目标日期数字 '{target_day_str}' 的文本: {day_texts}")

        # 策略1：如果日历已打开，先查找月份区块头部，然后在对应的日期区块中定位日期
        if calendar_opened:
            print("🔄 策略1：在日历中选择目标日期...")
            target_month = target.month
            target_day = target.day
            target_year = target.year
            target_day_str = str(target_day)
            target_month_str = f"{target_month}月"
            target_year_month_text = f"{target_year}年{target_month}月"
            target_month_text_short = f"{target_month}月"  # 也可能只有月份，没有年份
            print(f"🎯 目标日期: {target_year}年{target_month}月{target_day}日")

            # 刷新页面源码以获取最新的日历内容
            try:
                page = driver.page_source
                root = etree.fromstring(page.encode('utf-8'))
            except BaseException:

                page = driver.page_source
                root = etree.fromstring(page.encode('utf-8'))

            # 导入 parse_bounds 函数
            from utils import parse_bounds

            # 第一步：查找月份区块头部（如"2026年1月"或"1月"）
            month_header_element = None
            month_header_bounds = None
            found_target_month = False
            next_month_header_y = None  # 下一个月份标题的Y坐标，用于限制搜索范围

            try:
                all_elements = root.xpath('//*[@text and @bounds]')
                # 先找到所有月份标题，确定目标月份和下一个月份的位置
                month_headers = []
                for el in all_elements:
                    text = el.get('text', '').strip()
                    bounds = el.get('bounds', '')
                    bounds_tuple = parse_bounds(bounds)

                    if not bounds_tuple:
                        continue

                    # 匹配完整格式："2026年1月"或"2025年12月"等
                    year_month_match = re.match(r'^(\d{4})年(\d{1,2})月$', text)
                    if year_month_match:
                        year = int(year_month_match.group(1))
                        month = int(year_month_match.group(2))
                        month_headers.append({
                            'element': el,
                            'bounds': bounds_tuple,
                            'year': year,
                            'month': month,
                            'text': text,
                            'y': bounds_tuple[1]
                        })
                    # 匹配短格式："1月"或"12月"等
                    elif re.match(r'^\d{1,2}月$', text):

                        month_match = re.match(r'^(\d{1,2})月$', text)
                        if month_match:
                            month = int(month_match.group(1))
                            month_headers.append({
                                'element': el,
                                'bounds': bounds_tuple,
                                'year': None,  # 年份未知
                                'month': month,
                                'text': text,
                                'y': bounds_tuple[1]
                            })

                # 按Y坐标排序
                month_headers.sort(key=lambda x: x['y'])

                # 查找目标月份标题
                for header in month_headers:
                    # 匹配完整格式
                    if header['year'] == target_year and header['month'] == target_month:
                        month_header_element = header['element']
                        month_header_bounds = header['bounds']
                        found_target_month = True
                        print(f"✅ 找到目标月份标题: {header['text']}, Y={header['y']}")

                        # 查找下一个月份标题的Y坐标（用于限制搜索范围）
                        for next_header in month_headers:
                            if next_header['y'] > header['y']:
                                next_month_header_y = next_header['y']
                                print(f"📍 下一个月份标题位置: Y={next_month_header_y}")
                                break
                        break
                    # 匹配短格式（如果年份未知，但月份匹配）
                    elif header['year'] is None and header['month'] == target_month and not found_target_month:

                        month_header_element = header['element']
                        month_header_bounds = header['bounds']
                        print(
                            f"📅 找到月份标题: {header['text']}, Y={header['y']}，需要验证年份")

                        # 查找下一个月份标题的Y坐标
                        for next_header in month_headers:
                            if next_header['y'] > header['y']:
                                next_month_header_y = next_header['y']
                                print(f"📍 下一个月份标题位置: Y={next_month_header_y}")
                                break
            except Exception as e:

                print(f"⚠️ 查找月份标题失败: {e}")
                import traceback
                traceback.print_exc()

            # 第二步：如果没找到目标月份，尝试滑动查找
            max_scroll_attempts = 12  # 最多滑动12次（一年）
            scroll_attempt = 0

            while not found_target_month and scroll_attempt < max_scroll_attempts:
                # 刷新页面源码
                try:
                    page = driver.page_source
                    root = etree.fromstring(page.encode('utf-8'))
                    all_elements = root.xpath('//*[@text and @bounds]')

                    for el in all_elements:
                        text = el.get('text', '').strip()
                        # 匹配完整格式："2026年1月"
                        if text == target_year_month_text:
                            month_header_element = el
                            month_header_bounds = parse_bounds(
                                el.get('bounds', ''))
                            found_target_month = True
                            print(f"✅ 滑动后找到目标月份标题: {text}")
                            break
                        # 匹配短格式："1月"
                        elif text == target_month_text_short and not month_header_element:

                            month_header_element = el
                            month_header_bounds = parse_bounds(
                                el.get('bounds', ''))
                            print(f"📅 滑动后找到月份标题: {text}")
                except Exception as e:
                    print(f"⚠️ 刷新页面源码失败: {e}")

                if found_target_month:
                    break

                # 如果还没找到，向下滑动（显示下一个月）
                scroll_attempt += 1
                tprint(
                    f"🔄 未找到目标月份，向下滑动 ({scroll_attempt}/{max_scroll_attempts})...")
                try:
                    screen_size = driver.get_window_size()
                    driver.swipe(
                        screen_size['width'] // 2,
                        screen_size['height'] * 0.5,
                        screen_size['width'] // 2,
                        screen_size['height'] * 0.2,
                        500)
                    wait_step(driver, 1)
                except Exception as e:


                    tprint(f"⚠️ 滑动失败: {e}")

            # 第三步：如果找到了月份标题，重新刷新页面源码并重新定位月份标题（确保使用最新坐标）
            if month_header_element is not None:
                try:
                    # 重新刷新页面源码，确保获取最新的坐标
                    tprint("🔄 重新刷新页面源码以获取最新的月份标题位置...")
                    page = driver.page_source
                    root = etree.fromstring(page.encode('utf-8'))
                    all_elements = root.xpath('//*[@text and @bounds]')

                    # 重新查找月份标题，确保使用最新的坐标
                    month_header_bounds = None
                    next_month_header_y = None
                    month_headers = []

                    for el in all_elements:
                        text = el.get('text', '').strip()
                        bounds = el.get('bounds', '')
                        bounds_tuple = parse_bounds(bounds)

                        if not bounds_tuple:
                            continue

                        # 匹配完整格式："2026年2月"
                        if text == target_year_month_text:
                            month_header_bounds = bounds_tuple
                            print(f"✅ 重新定位目标月份标题: {text}, Y={bounds_tuple[1]}")
                            # 继续查找下一个月份标题
                            for next_el in all_elements:
                                next_text = next_el.get('text', '').strip()
                                next_bounds = parse_bounds(
                                    next_el.get('bounds', ''))
                                if next_bounds and next_bounds[1] > bounds_tuple[1]:
                                    # 检查是否是月份标题格式
                                    if re.match(
                                            r'^(\d{4})年(\d{1,2})月$',
                                            next_text) or re.match(
                                            r'^\d{1,2}月$',
                                            next_text):
                                        next_month_header_y = next_bounds[1]
                                        print(
                                            f"📍 重新定位下一个月份标题位置: Y={next_month_header_y}")
                                        break
                            break
                        # 匹配短格式："2月"（如果之前找到的是短格式）
                        elif text == target_month_text_short and month_header_bounds is None:
                            month_header_bounds = bounds_tuple
                            print(f"📅 重新定位月份标题: {text}, Y={bounds_tuple[1]}")

                    if month_header_bounds is None:
                        print(f"⚠️ 重新定位失败，使用之前找到的月份标题位置")
                        # 如果重新定位失败，使用之前找到的位置
                        if month_header_element is not None:
                            old_bounds = month_header_element.get('bounds', '')
                            month_header_bounds = parse_bounds(old_bounds)
                except Exception as e:

                    print(f"⚠️ 重新定位月份标题失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 如果重新定位失败，使用之前找到的位置
                    if month_header_element is not None:
                        old_bounds = month_header_element.get('bounds', '')
                        month_header_bounds = parse_bounds(old_bounds)

            if month_header_bounds is not None:
                month_header_y = month_header_bounds[1]  # 月份标题的顶部Y坐标
                month_header_bottom = month_header_bounds[3]  # 月份标题的底部Y坐标
                print(f"📍 月份标题位置: Y={month_header_y} 到 {month_header_bottom}")

                # 检查月份标题是否在可见范围内，如果不在，需要向上滑动日历
                screen_size = driver.get_window_size()
                screen_height = screen_size['height']
                visible_top = 0
                visible_bottom = screen_height * 0.9  # 可见区域的底部（留10%的缓冲）

                # 如果月份标题的Y坐标超出可见范围（在屏幕底部以下），需要向上滑动
                if month_header_y > visible_bottom:
                    print(
                        f"⚠️ 月份标题Y坐标({month_header_y})超出可见范围({visible_bottom})，需要向上滑动日历...")
                    max_scroll_up_attempts = 5
                    scroll_up_attempt = 0

                    while month_header_y > visible_bottom and scroll_up_attempt < max_scroll_up_attempts:
                        scroll_up_attempt += 1
                        tprint(
                            f"🔄 向上滑动日历以显示月份标题 ({scroll_up_attempt}/{max_scroll_up_attempts})...")
                        try:
                            # 向上滑动：从屏幕中间向上滑动，显示下面的内容（月份标题在下方）
                            # 注意：向上滑动意味着从下往上滑动，显示上面的内容
                            driver.swipe(
                                screen_size['width'] // 2,
                                screen_height * 0.7,
                                screen_size['width'] // 2,
                                screen_height * 0.3,
                                500)
                            wait_step(driver, 1)

                            # 重新刷新页面源码并重新定位月份标题
                            page = driver.page_source
                            root = etree.fromstring(page.encode('utf-8'))
                            all_elements = root.xpath('//*[@text and @bounds]')

                            # 重新查找月份标题
                            for el in all_elements:
                                text = el.get('text', '').strip()
                                bounds = el.get('bounds', '')
                                bounds_tuple = parse_bounds(bounds)

                                if not bounds_tuple:
                                    continue

                                if text == target_year_month_text:
                                    month_header_bounds = bounds_tuple
                                    month_header_y = bounds_tuple[1]
                                    month_header_bottom = bounds_tuple[3]
                                    print(
                                        f"✅ 滑动后重新定位月份标题: {text}, Y={month_header_y}")
                                    break
                                elif text == target_month_text_short and month_header_bounds is None:

                                    month_header_bounds = bounds_tuple
                                    month_header_y = bounds_tuple[1]
                                    month_header_bottom = bounds_tuple[3]
                                    print(
                                        f"📅 滑动后重新定位月份标题: {text}, Y={month_header_y}")

                            # 如果月份标题现在在可见范围内，停止滑动
                            if month_header_y <= visible_bottom:
                                print(f"✅ 月份标题已进入可见范围: Y={month_header_y}")
                                break
                        except Exception as e:

                            tprint(f"⚠️ 向上滑动失败: {e}")
                            break

                    if month_header_y > visible_bottom:
                        print(
                            f"⚠️ 滑动后月份标题Y坐标({month_header_y})仍超出可见范围，但继续尝试搜索日期...")

                # 确定搜索范围：从月份标题下方到下一个月份标题（如果存在）
                search_y_min = month_header_bottom  # 搜索范围的最小Y坐标
                search_y_max = next_month_header_y if next_month_header_y else float(
                    'inf')  # 搜索范围的最大Y坐标
                print(
                    f"📍 日期搜索范围: Y={search_y_min} 到 {search_y_max if search_y_max != float('inf') else '屏幕底部'}")

                # 查找该月份标题下方的所有日期元素
                target_day_element = None
                min_distance = float('inf')

                try:
                    # 重新刷新页面源码，确保使用最新的页面状态（可能已经滑动过）
                    page = driver.page_source
                    root = etree.fromstring(page.encode('utf-8'))
                    all_elements = root.xpath('//*[@text and @bounds]')

                    # 重新定位月份标题位置（确保使用最新的坐标）
                    current_month_header_y = None
                    current_month_header_bottom = None
                    for el in all_elements:
                        el_text = el.get('text', '').strip()
                        if el_text == target_year_month_text or el_text == target_month_text_short:
                            el_bounds = parse_bounds(el.get('bounds', ''))
                            if el_bounds:
                                current_month_header_y = el_bounds[1]
                                current_month_header_bottom = el_bounds[3]
                                break

                    # 如果找到了月份标题，更新搜索范围
                    if current_month_header_y is not None:
                        month_header_y = current_month_header_y
                        month_header_bottom = current_month_header_bottom
                        search_y_min = month_header_bottom
                        print(
                            f"🔄 重新定位月份标题位置: Y={month_header_y}, 底部={month_header_bottom}")
                        print(
                            f"📍 更新后的日期搜索范围: Y={search_y_min} 到 {search_y_max if search_y_max != float('inf') else '屏幕底部'}")

                    for el in all_elements:
                        text = el.get('text', '').strip()
                        bounds = el.get('bounds', '')
                        bounds_tuple = parse_bounds(bounds)

                        if not bounds_tuple:
                            continue

                        el_y = bounds_tuple[1]  # 元素的顶部Y坐标
                        el_center_y = (
                            bounds_tuple[1] + bounds_tuple[3]) / 2  # 元素的中心Y坐标

                        # 检查是否是目标日期数字（纯数字且等于目标日期）
                        if text == target_day_str:
                            # 严格检查：元素必须在月份标题下方，且在下一个月份标题之前（如果存在）
                            if el_y >= search_y_min and el_center_y < search_y_max:
                                # 额外验证：检查日期元素周围是否有目标月份的相关文本（更严格的验证）
                                # 查找日期元素附近的元素，检查是否有月份相关的文本
                                is_in_target_month = True
                                if current_month_header_y is not None:
                                    # 检查日期元素是否在月份标题和下一个月份标题之间
                                    # 同时检查日期元素附近是否有其他月份的标题（如果日期元素上方有其他月份标题，则不是目标月份）
                                    for nearby_el in all_elements:
                                        nearby_text = nearby_el.get(
                                            'text', '').strip()
                                        nearby_bounds = parse_bounds(
                                            nearby_el.get('bounds', ''))
                                        if nearby_bounds:
                                            nearby_y = nearby_bounds[1]
                                            # 如果日期元素上方有其他月份标题，且该月份标题在目标月份标题下方，则这个日期元素可能不在目标月份内
                                            if nearby_y < el_y and nearby_y > month_header_bottom:
                                                # 检查是否是月份标题格式
                                                if ('月' in nearby_text and '年' in nearby_text) or (
                                                        nearby_text.endswith('月') and len(nearby_text) <= 4):
                                                    # 如果找到的月份标题不是目标月份，则这个日期元素不在目标月份内
                                                    if nearby_text != target_year_month_text and nearby_text != target_month_text_short:
                                                        is_in_target_month = False
                                                        print(
                                                            f"⚠️ 日期元素 {text} 上方发现其他月份标题: {nearby_text}，跳过")
                                                        break

                                if is_in_target_month:
                                    # 计算与月份标题的距离（优先选择最近的）
                                    distance = el_y - month_header_y
                                    if distance < min_distance:
                                        min_distance = distance
                                        target_day_element = el
                                        print(
                                            f"📅 找到候选日期元素: {text}, 位置: Y={el_y}, 中心Y={el_center_y:.0f}, 距离: {distance}")
                            else:
                                print(
                                    f"⚠️ 日期元素 {text} 位置 Y={el_y} 不在搜索范围内（{search_y_min} 到 {search_y_max if search_y_max != float('inf') else '屏幕底部'}），跳过")
                except Exception as e:

                    print(f"⚠️ 查找日期元素失败: {e}")
                    import traceback
                    traceback.print_exc()

                # 如果找到了目标日期元素，点击它
                if target_day_element is not None:
                    try:
                        day_text = target_day_element.get('text', '').strip()
                        # 使用更精确的定位方式：结合文本和位置
                        bounds_tuple = parse_bounds(
                            target_day_element.get('bounds', ''))
                        if bounds_tuple:
                            # 尝试使用坐标点击，更精确
                            center_x = (bounds_tuple[0] + bounds_tuple[2]) // 2
                            center_y = (bounds_tuple[1] + bounds_tuple[3]) // 2
                            try:
                                driver.tap([(center_x, center_y)], 100)
                                tprint(
                                    f"✅ 成功点击目标日期: {day_text} (在 {target_year}年{target_month}月 区块中, 坐标: ({center_x}, {center_y}))")
                                wait_step(driver, 1)
                                return True
                            except BaseException:

                                # 如果坐标点击失败，尝试文本点击
                                el_click = driver.find_element(
                                    AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{day_text}")')
                                el_click.click()
                                tprint(
                                    f"✅ 成功点击目标日期: {day_text} (在 {target_year}年{target_month}月 区块中)")
                                wait_step(driver, 1)
                                return True
                            except BaseException:

                                # 如果坐标点击失败，尝试文本点击
                                el_click = driver.find_element(
                                    AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{day_text}")')
                                el_click.click()
                                tprint(
                                    f"✅ 成功点击目标日期: {day_text} (在 {target_year}年{target_month}月 区块中)")
                                wait_step(driver, 1)
                                return True
                    except Exception as e:

                        traceback.print_exc()
                    else:
                        print(
                            f"⚠️ 在 {target_year}年{target_month}月 区块中未找到日期 {target_day}日")
                    print(
                        f"   搜索范围: Y={search_y_min} 到 {search_y_max if search_y_max != float('inf') else '屏幕底部'}")
            else:
                print(
                    f"⚠️ 未找到目标月份标题: {target_year_month_text} 或 {target_month_text_short}")

            # 第四步：如果上述方法都失败，尝试备用方法（直接查找日期数字，但需要更严格的筛选）
            # 注意：只有在没有找到月份标题时才使用备用方法
            if not found_target_month:
                print("🔄 尝试备用方法：直接查找日期数字...")
                try:
                    page = driver.page_source
                    root = etree.fromstring(page.encode('utf-8'))
                    all_elements = root.xpath('//*[@text and @bounds]')

                    # 查找所有包含目标日期数字的元素
                    candidate_elements = []
                    for el in all_elements:
                        text = el.get('text', '').strip()
                        if text == target_day_str:  # 只匹配纯数字
                            bounds_tuple = parse_bounds(el.get('bounds', ''))
                            if bounds_tuple:
                                candidate_elements.append((el, bounds_tuple))

                    if candidate_elements:
                        print(
                            f"📅 找到 {len(candidate_elements)} 个日期数字 '{target_day_str}' 的候选元素")
                        # 选择Y坐标最大的（通常是最下方的，可能是目标月份）
                        candidate_elements.sort(
                            key=lambda x: x[1][1], reverse=True)
                        # 尝试点击第一个候选元素
                        # 最多尝试前3个
                        for el, bounds_tuple in candidate_elements[:3]:
                            try:
                                el_click = driver.find_element(
                                    AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{target_day_str}")')
                                el_click.click()
                                print(f"✅ 备用方法：成功点击日期数字: {target_day_str}")
                                wait_step(driver, 1)
                                return True
                            except BaseException:
                                continue
                except Exception as e:
                    print(f"⚠️ 备用方法失败: {e}")
            
            # 如果所有方法都失败
            print("❌ 所有尝试失败，无法找到目标日期")
            print(f"❌ 目标日期: {target_year}年{target_month}月{target_day}日")
            print(f"❌ 当前日期: {today.strftime('%Y-%m-%d')}")
            return False

        # 策略2：如果日历未打开，尝试候选文案点击
        if not calendar_opened:
            print("🔄 策略2：日历未打开，尝试候选文案点击...")
            for label in candidates:
                if label in visible_texts:
                    try:
                        el = driver.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().text("{label}")')
                        el.click()
                        print(f"✅ 策略2成功：已选择目标日期: {label}")
                        wait_step(driver, 1)
                        return True
                    except Exception as e:

                        print(f"⚠️ 文案存在但点击失败: {label}, {e}")
        
        print(f"❌ 所有策略失败，无法选择日期: {depart_date}")
        return False

    except Exception as e:


        print(f"❌ 日期选择流程异常: {e}")
        return False


