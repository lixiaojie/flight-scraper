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
from utils import tprint
from capture_utils import extract_flight_elements_from_xml

def find_scrollable_list(driver):
    """
    查找页面中间的可滚动列表元素
    
    Returns:
        dict or None: 包含元素信息的字典 {'element': WebElement, 'location': dict, 'size': dict}
    """
    try:
        screen_size = driver.get_window_size()
        screen_center_y = screen_size['height'] / 2
        
        # 尝试查找所有可滚动元素，然后筛选出在中间区域的
        try:
            scrollable_elements = driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().scrollable(true)')
            
            print(f"🔍 找到 {len(scrollable_elements)} 个可滚动元素")
            
            # 找到位置在中间区域的元素（排除顶部25%和底部25%）
            for element in scrollable_elements:
                try:
                    location = element.location
                    size = element.size
                    
                    # 计算元素中心点Y坐标
                    element_center_y = location['y'] + size['height'] / 2
                    element_top = location['y']
                    element_bottom = location['y'] + size['height']
                    
                    # 检查元素是否主要在中间区域（顶部在25%-60%之间，底部在40%-75%之间）
                    # 并且高度足够大（至少占据屏幕的20%）
                    if (screen_size['height'] *
                        0.25 <= element_top <= screen_size['height'] *
                        0.6 and screen_size['height'] *
                        0.4 <= element_bottom <= screen_size['height'] *
                        0.75 and size['height'] >= screen_size['height'] *
                            0.2):
                        print(
                            f"✅ 找到中间区域的可滚动元素: 位置 {location}, 大小 {size}, 中心Y: {element_center_y}")
                        return {
                            'element': element,
                            'location': location,
                            'size': size,
                            'center_y': element_center_y
                        }
                except Exception as e:

                    continue
            
            # 如果没有找到完全符合条件的，选择最接近中间的可滚动元素
            best_element = None
            best_distance = float('inf')
            
            for element in scrollable_elements:
                try:
                    location = element.location
                    size = element.size
                    element_center_y = location['y'] + size['height'] / 2
                    
                    # 计算到屏幕中心的距离
                    distance = abs(element_center_y - screen_center_y)
                    
                    # 如果元素在中间区域且距离更近，选择它
                    if (screen_size['height'] *
                        0.2 <= element_center_y <= screen_size['height'] *
                            0.8 and distance < best_distance):
                        best_distance = distance
                        best_element = {
                            'element': element,
                            'location': location,
                            'size': size,
                            'center_y': element_center_y
                        }
                except BaseException:

                    continue
            
            if best_element:
                print(
                    f"✅ 选择最接近中间的可滚动元素: 位置 {best_element['location']}, 大小 {best_element['size']}")
                return best_element
                
        except Exception as e:
            print(f"⚠️ 查找可滚动元素时出错: {e}")
        
        print("⚠️ 未找到可滚动列表元素，将使用页面中间区域进行滚动")
        return None
    except Exception as e:
        print(f"⚠️ 查找可滚动列表时出错: {e}")
        return None



def swipe_down_in_middle(driver, scrollable_info=None, use_w3c_actions=True):
    """
    在页面中间区域模拟向下滑动操作（向下滚动，显示下面的内容）。
    针对可滚动区域进行滑动，避免触碰头部和底部固定区域。
    优先使用 W3C Actions API，如果失败则回退到传统 swipe 方法。

    注意：要显示下面的内容，需要从下方滑向上方（start_y > end_y）
    
    Args:
        driver: WebDriver实例
        scrollable_info: 可滚动元素的信息字典（如果为None，则在页面中间区域滑动）
        use_w3c_actions: 是否使用 W3C Actions API（默认True）
    """
    screen_size = driver.get_window_size()
    start_x = screen_size['width'] // 2
    
    # 计算滑动坐标
    # 要显示下面的内容，需要从下方滑向上方（start_y > end_y）
    if scrollable_info and 'location' in scrollable_info and 'size' in scrollable_info:
        try:
            # 获取可滚动元素的位置和大小
            location = scrollable_info['location']
            size = scrollable_info['size']
            
            # 在可滚动元素的中间区域进行滑动（从下方滑向上方，显示下面的内容）
            # 使用更小的滑动范围，确保只触发列表滚动而不拖动整个页面
            start_y = location['y'] + size['height'] * 0.6  # 元素下方60%处（起点）
            end_y = location['y'] + size['height'] * 0.4    # 元素上方40%处（终点）

            # 确保坐标在屏幕范围内，并且滑动距离不要太大
            start_y = max(50, min(start_y, screen_size['height'] - 50))
            end_y = max(50, min(end_y, screen_size['height'] - 50))
            
            # 限制滑动距离，避免拖动整个页面（最大滑动距离为屏幕高度的20%）
            swipe_distance = abs(start_y - end_y)
            max_swipe_distance = screen_size['height'] * 0.2
            if swipe_distance > max_swipe_distance:
                end_y = start_y - max_swipe_distance

            print(
                f"📍 在可滚动元素内向下滑动（显示下面的内容）: 从 Y={start_y:.0f} 到 Y={end_y:.0f} (元素位置: {location}, 大小: {size})")
        except Exception as e:

            print(f"⚠️ 在可滚动元素内滑动失败: {e}，回退到中间区域滑动")
            # 使用页面高度的70%到30%进行滑动（从下方滑向上方，显示下面的内容，增加滚动距离）
            start_y = screen_size['height'] * 0.7  # 从屏幕下方70%开始
            end_y = screen_size['height'] * 0.3   # 滑动到屏幕上方30%
    else:
        # 备用方案：在页面中间区域向下滑动（从下方滑向上方，显示下面的内容）
        # 限制在中间区域，避免触碰顶部和底部固定区域
        start_y = screen_size['height'] * 0.7  # 从屏幕下方70%开始（起点，增加滚动距离）
        end_y = screen_size['height'] * 0.3     # 滑动到屏幕上方30%（终点，增加滚动距离）
        # 确保滑动距离足够，触发列表滚动
        swipe_distance = abs(start_y - end_y)
        if swipe_distance > screen_size['height'] * 0.5:
            # 如果距离太大，限制在屏幕高度的40%以内
            end_y = start_y - screen_size['height'] * 0.4
        print(
            f"📍 在页面中间区域向下滑动（显示下面的内容）: 从 Y={start_y:.0f} (页面高度70%) 到 Y={end_y:.0f} (页面高度30%)")
    
    # 优先使用 W3C Actions API
    if use_w3c_actions:
        try:
            actions = ActionChains(driver)
            actions.w3c_actions = ActionBuilder(
                driver, mouse=PointerInput(
                    interaction.POINTER_TOUCH, "touch"))
            actions.w3c_actions.pointer_action.move_to_location(
                int(start_x), int(start_y))
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.move_to_location(
                int(start_x), int(end_y))
            actions.w3c_actions.pointer_action.pause(0.25)  # 添加暂停，模拟真实触摸
            actions.w3c_actions.pointer_action.release()
            actions.perform()
            return
        except Exception as e:

            print(f"⚠️ W3C Actions API 滑动失败: {e}，回退到传统 swipe 方法")
    
    # 回退到传统 swipe 方法
    # 使用更短的持续时间（500ms而不是800ms），使滑动更精确
    try:
        driver.swipe(int(start_x), int(start_y), int(start_x), int(end_y), 500)
    except Exception as e:

        print(f"⚠️ 传统 swipe 方法也失败: {e}")



def swipe_up_in_middle(driver, scrollable_info=None, use_w3c_actions=True):
    """
    在页面中间区域模拟向上滑动操作（向上滚动，显示上面的内容）。
    针对可滚动区域进行滑动，避免触碰头部和底部固定区域。
    优先使用 W3C Actions API，如果失败则回退到传统 swipe 方法。
    
    Args:
        driver: WebDriver实例
        scrollable_info: 可滚动元素的信息字典（如果为None，则在页面中间区域滑动）
        use_w3c_actions: 是否使用 W3C Actions API（默认True）
    """
    screen_size = driver.get_window_size()
    start_x = screen_size['width'] // 2
    
    # 计算滑动坐标（向上滑动：从下往上，start_y > end_y）
    if scrollable_info and 'location' in scrollable_info and 'size' in scrollable_info:
        try:
            # 获取可滚动元素的位置和大小
            location = scrollable_info['location']
            size = scrollable_info['size']
            
            # 在可滚动元素的中间区域进行反向滑动（从下往上，使用更小的范围60%-40%）
            start_y = location['y'] + size['height'] * 0.6  # 元素下方60%处
            end_y = location['y'] + size['height'] * 0.4      # 元素上方40%处

            # 确保坐标在屏幕范围内，并且滑动距离不要太大
            start_y = max(50, min(start_y, screen_size['height'] - 50))
            end_y = max(50, min(end_y, screen_size['height'] - 50))
            
            # 限制滑动距离，避免拖动整个页面（最大滑动距离为屏幕高度的20%）
            swipe_distance = abs(end_y - start_y)
            max_swipe_distance = screen_size['height'] * 0.2
            if swipe_distance > max_swipe_distance:
                end_y = start_y + max_swipe_distance

            print(
                f"📍 在可滚动元素内向上滑动（显示上面的内容）: 从 Y={start_y:.0f} 到 Y={end_y:.0f} (元素位置: {location}, 大小: {size})")
        except Exception as e:

            print(f"⚠️ 在可滚动元素内向上滑动失败: {e}，回退到中间区域滑动")
            # 使用页面高度的30%到70%进行滑动（增加滚动距离）
            start_y = screen_size['height'] * 0.3
            end_y = screen_size['height'] * 0.7
    else:
        # 备用方案：在页面中间区域向上滑动（使用更大的范围30%-70%，增加滚动距离）
        start_y = screen_size['height'] * 0.3  # 从屏幕上方30%开始
        end_y = screen_size['height'] * 0.7    # 滑动到屏幕下方70%
        # 确保滑动距离足够，触发列表滚动
        swipe_distance = abs(end_y - start_y)
        if swipe_distance > screen_size['height'] * 0.5:
            # 如果距离太大，限制在屏幕高度的40%以内
            end_y = start_y + screen_size['height'] * 0.4
        print(
            f"📍 在页面中间区域向上滑动（显示上面的内容）: 从 Y={start_y:.0f} (页面高度30%) 到 Y={end_y:.0f} (页面高度70%)")
    
    # 优先使用 W3C Actions API
    if use_w3c_actions:
        try:
            actions = ActionChains(driver)
            actions.w3c_actions = ActionBuilder(
                driver, mouse=PointerInput(
                    interaction.POINTER_TOUCH, "touch"))
            actions.w3c_actions.pointer_action.move_to_location(
                int(start_x), int(start_y))
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.move_to_location(
                int(start_x), int(end_y))
            actions.w3c_actions.pointer_action.pause(0.25)  # 添加暂停，模拟真实触摸
            actions.w3c_actions.pointer_action.release()
            actions.perform()
            return
        except Exception as e:

            print(f"⚠️ W3C Actions API 向上滑动失败: {e}，回退到传统 swipe 方法")
    
    # 回退到传统 swipe 方法
    # 使用更短的持续时间（500ms而不是800ms），使滑动更精确
    try:
        driver.swipe(int(start_x), int(start_y), int(start_x), int(end_y), 500)
    except Exception as e:

        print(f"⚠️ 传统 swipe 方法也失败: {e}")



def scroll_to_top(driver, use_w3c_actions=True):
    """
    滚动到页面顶部
    优先使用 UiScrollable，失败则使用 W3C Actions API 或传统 swipe
    """
    print("🔄 滚动到页面顶部...")
    try:
        # 优先使用 UiScrollable 滚动到顶部
        driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
                          'new UiScrollable(new UiSelector().scrollable(true)).scrollToBeginning(5)')
        time.sleep(1)
        return True
    except Exception as e:

        print(f"⚠️ UiScrollable滚动到顶部失败，使用备用方法: {e}")
        # 备用方案：从下往上swipe多次（向上滚动，回到顶部）
        screen_size = driver.get_window_size()
        start_x = screen_size['width'] // 2
        start_y = screen_size['height'] * 0.8
        end_y = screen_size['height'] * 0.2
        
        for _ in range(5):
            if use_w3c_actions:
                try:
                    actions = ActionChains(driver)
                    actions.w3c_actions = ActionBuilder(
                        driver, mouse=PointerInput(
                            interaction.POINTER_TOUCH, "touch"))
                    actions.w3c_actions.pointer_action.move_to_location(
                        int(start_x), int(start_y))
                    actions.w3c_actions.pointer_action.pointer_down()
                    actions.w3c_actions.pointer_action.move_to_location(
                        int(start_x), int(end_y))
                    actions.w3c_actions.pointer_action.pause(0.25)
                    actions.w3c_actions.pointer_action.release()
                    actions.perform()
                except BaseException:

                    # W3C Actions 失败，使用传统方法
                    driver.swipe(
                        int(start_x),
                        int(start_y),
                        int(start_x),
                        int(end_y),
                        1000)
            else:
                driver.swipe(
                    int(start_x),
                    int(start_y),
                    int(start_x),
                    int(end_y),
                    1000)
            time.sleep(0.5)
        return False



def perform_scroll_forward(driver, scroll_steps=3, scrollable_info=None):
    """
    执行方式1：使用scrollForward滚动，针对可滚动列表元素
    优先尝试UiScrollable，失败则使用中间区域swipe
    
    Args:
        driver: WebDriver实例
        scroll_steps: 滚动步数
        scrollable_info: 可滚动元素信息字典（可选）
    
    Returns:
        bool: 是否滚动成功
    """
    try:
        if driver.capabilities.get('platformName') == 'Android':
            # 优先尝试使用UiScrollable（它会自动找到可滚动元素）
            try:
                driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                                  f'new UiScrollable(new UiSelector().scrollable(true)).setAsVerticalList().scrollForward({scroll_steps})')
                return True
            except BaseException:

                # UiScrollable失败，使用中间区域swipe
                swipe_down_in_middle(driver, scrollable_info)
                return True
        else:
            swipe_down_in_middle(driver, scrollable_info)
            return True
    except Exception as e:


        # 如果都失败，尝试swipe
        try:
            swipe_down_in_middle(driver, scrollable_info)
            return True
        except BaseException:

            return False



def perform_scroll_backward(driver, scroll_steps=3, scrollable_info=None):
    """
    执行方式2：使用scrollBackward滚动，针对可滚动列表元素
    优先尝试UiScrollable，失败则使用中间区域swipe
    
    Args:
        driver: WebDriver实例
        scroll_steps: 滚动步数
        scrollable_info: 可滚动元素信息字典（可选）
    
    Returns:
        bool: 是否滚动成功
    """
    try:
        if driver.capabilities.get('platformName') == 'Android':
            # 优先尝试使用UiScrollable
            try:
                driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                                  f'new UiScrollable(new UiSelector().scrollable(true)).setAsVerticalList().scrollBackward({scroll_steps})')
                return True
            except BaseException:

                # UiScrollable失败，使用中间区域反向swipe（向上滑动）
                swipe_up_in_middle(driver, scrollable_info)
                return True
        else:
            # 对于非Android，在中间区域反向滑动（向上滑动）
            swipe_up_in_middle(driver, scrollable_info)
            return True
    except Exception as e:


        return False



def perform_scroll_swipe(driver, scrollable_info=None, direction='down'):
    """
    执行方式3：使用swipe在中间区域滚动（备用方案）
    
    Args:
        driver: WebDriver实例
        scrollable_info: 可滚动元素信息字典（可选）
        direction: 滚动方向，'down'（向下，显示下面内容）或'up'（向上，显示上面内容）
    
    Returns:
        bool: 是否滚动成功
    """
    try:
        if direction == 'down':
            swipe_down_in_middle(driver, scrollable_info)
        else:
            swipe_up_in_middle(driver, scrollable_info)
        return True
    except Exception as e:

        return False



def perform_scroll(driver, scroll_steps=3):
    """
    执行滚动操作（兼容旧代码）
    
    Args:
        driver: WebDriver实例
        scroll_steps: UiScrollable的滚动步数
    
    Returns:
        bool: 是否滚动成功
    """
    # 默认尝试方式1
    if perform_scroll_forward(driver, scroll_steps):
        return True
    # 失败则尝试方式2
    if perform_scroll_backward(driver, scroll_steps):
        return True
    # 都失败则使用swipe
    return perform_scroll_swipe(driver)



def smart_scroll_and_capture(driver, output_dir):
    """
    使用智能滚动策略：先测试两种滚动方式，找到有效方式后持续使用，
    当有效方式失效时重新测试两种方式，都失效才结束
    针对页面中间的可滚动区域进行滚动，避免触碰头部和底部固定区域
    """
    print("🔄 开始智能滚动以加载所有航班信息...")
    
    # 等待页面完全加载
    time.sleep(3)
    
    # 查找页面中间的可滚动列表元素
    print("🔍 查找页面中间的可滚动列表区域...")
    scrollable_info = find_scrollable_list(driver)
    
    # 使用set数据结构自动去重，存储所有抓取到的元素
    all_elements_text = set()
    unique_flights = set()
    max_scrolls = 50  # 增加最大滚动次数限制
    scroll_count = 0
    stable_count = 0  # 连续无变化的次数
    effective_scroll_method = None  # 当前有效的滚动方式：'forward', 'backward', 'swipe', None
    
    # 定义滚动方式（传入scrollable_info参数）
    scroll_methods = [
        ('forward',
         lambda: perform_scroll_forward(
             driver,
             3,
             scrollable_info),
            'scrollForward'),
        ('backward',
         lambda: perform_scroll_backward(
             driver,
             3,
             scrollable_info),
            'scrollBackward'),
    ]

    # 滚动到页面顶部（确保从页头开始）
    print("📍 滚动到页面顶部，准备从页头开始逐步向下滚动...")
    scroll_to_top(driver)
    time.sleep(2)  # 等待滚动到顶部完成
    
    print("🔄 开始智能滚动并提取页面内容（从页头逐步向下滚动到页尾）...")
    min_scrolls = 5  # 最小滚动次数，确保至少滚动多次以加载所有内容
    initial_scrolls = 0
    while max_scrolls > 0:
        scroll_count += 1
        initial_scrolls += 1
        print(f"🔄 第{scroll_count}次滚动...")
        
        # 1. 如果是第一次迭代，直接获取初始page_source；否则先滚动再获取
        if scroll_count == 1:
            # 第一次迭代：直接获取初始页面内容
            try:
                current_page_source = driver.page_source
            except Exception as e:

                print(f"⚠️ 获取页面源码失败: {e}")
                break
        else:
            # 后续迭代：先执行滚动操作，然后等待，再获取新的page_source
            if effective_scroll_method:
                # 使用有效的滚动方式（统一使用向下滚动以加载更多内容）
                if effective_scroll_method.startswith('swipe_'):
                    # 如果之前测试的是swipe_up，说明向上滚动有效，但我们需要向下滚动加载更多
                    # 所以统一使用向下滚动
                    perform_scroll_swipe(
                        driver, scrollable_info, direction='down')
                elif effective_scroll_method == 'forward':

                    perform_scroll_forward(driver, 3, scrollable_info)
                elif effective_scroll_method == 'backward':

                    perform_scroll_backward(driver, 3, scrollable_info)
                else:
                    # 默认向下滚动以加载更多内容
                    perform_scroll_swipe(
                        driver, scrollable_info, direction='down')
            else:
                # 没有有效方式，默认向下滚动以加载更多内容
                perform_scroll_swipe(driver, scrollable_info, direction='down')
            
            # 等待滚动完成和内容加载（增加等待时间确保内容完全加载）
            time.sleep(3.0)
            
            # 获取滚动后的page_source
            try:
                current_page_source = driver.page_source
            except Exception as e:

                print(f"⚠️ 获取页面源码失败: {e}")
                break
        
        # 2. 解析 XML，提取所有可见区域内容（不传入driver，读取全部内容以确保不遗漏）
        # 注意：传入driver=None以读取所有displayed="true"的元素，不限制bounds
        current_flights, current_elements_text, current_element_count = extract_flight_elements_from_xml(
            current_page_source, driver=None)
        
        # 调试信息：打印提取到的航班号
        if current_flights:
            print(f"🔍 本次提取到航班号: {sorted(current_flights)}")
        
        # 记录更新前的数量
        previous_flight_count = len(unique_flights)
        previous_elements_count = len(all_elements_text)
        
        # 3. 更新全局集合
        all_elements_text.update(current_elements_text)
        unique_flights.update(current_flights)
        
        # 4. 检查是否有新内容
        all_elements_count_after = len(all_elements_text)
        new_elements_count = all_elements_count_after - previous_elements_count
        current_flight_count = len(unique_flights)
        new_flights_count = current_flight_count - previous_flight_count
        
        print(f"📊 当前元素数量: {current_element_count}, 总元素数: {all_elements_count_after}, "
              f"新增元素: {new_elements_count}, 唯一航班: {current_flight_count}, 新增航班: {new_flights_count}")
        
        # 判断是否有新内容
        has_new_content = new_elements_count > 0 or new_flights_count > 0
        
        if has_new_content:
            # 有新内容，重置稳定计数
            stable_count = 0
            print(f"✅ 发现新内容（元素+{new_elements_count}, 航班+{new_flights_count}）")
        
        # 如果没有有效的滚动方式，测试所有方式找到有效的
        if not effective_scroll_method:
            print("🔍 测试所有滚动方式以找到有效方式...")
            method_found = False
            
            for method_name, scroll_func, method_desc in scroll_methods:
                print(f"  🧪 测试方式: {method_desc}")
                
                # 记录测试前的状态
                test_before_elements = len(all_elements_text)
                test_before_flights = len(unique_flights)
                
                # 执行滚动
                if scroll_func():
                    time.sleep(2.5)  # 增加等待时间，确保WebView内容加载完成
                    
                    # 获取滚动后的页面状态
                    try:
                        test_page_source = driver.page_source
                        # 使用driver=None以读取所有可见内容，不限制bounds
                        test_flights, test_elements_text, _ = extract_flight_elements_from_xml(
                            test_page_source, driver=None)
                        
                        # 检查是否有新内容
                        all_elements_text.update(test_elements_text)
                        unique_flights.update(test_flights)
                        
                        test_after_elements = len(all_elements_text)
                        test_after_flights = len(unique_flights)
                        
                        test_new_elements = test_after_elements - test_before_elements
                        test_new_flights = test_after_flights - test_before_flights
                        
                        if test_new_elements > 0 or test_new_flights > 0:
                            effective_scroll_method = method_name
                            method_found = True
                            print(
                                f"  ✅ 方式 {method_desc} 有效！发现新内容（元素+{test_new_elements}, 航班+{test_new_flights}）")
                            print(f"  📌 将使用方式: {method_desc}")
                            break
                        else:
                            print(f"  ❌ 方式 {method_desc} 未发现新内容")
                            # 回滚状态
                            # 注意：这里不能完全回滚，因为可能已经加载了部分内容
                    except Exception as e:

                        print(f"  ⚠️ 测试方式 {method_desc} 时出错: {e}")
                else:
                    print(f"  ❌ 方式 {method_desc} 执行失败")
            
            if not method_found:
                # 如果所有方式都无效，尝试swipe down方式（向下滚动以加载更多内容）
                swipe_dir = 'down'
                print(f"  🧪 测试备用方式: swipe {swipe_dir} (中间区域)")
                test_before_elements = len(all_elements_text)
                test_before_flights = len(unique_flights)
                
                if perform_scroll_swipe(
                        driver, scrollable_info, direction=swipe_dir):
                    # 增加等待时间，确保WebView内容完全加载
                    time.sleep(3.0)
                    try:
                        test_page_source = driver.page_source
                        # 提取所有可见区域的内容（不限制bounds，因为滚动可能加载了屏幕外的内容）
                        test_flights, test_elements_text, _ = extract_flight_elements_from_xml(
                            test_page_source, driver=None)
                        
                        all_elements_text.update(test_elements_text)
                        unique_flights.update(test_flights)
                        
                        test_after_elements = len(all_elements_text)
                        test_after_flights = len(unique_flights)
                        
                        test_new_elements = test_after_elements - test_before_elements
                        test_new_flights = test_after_flights - test_before_flights
                        
                        if test_new_elements > 0 or test_new_flights > 0:
                            effective_scroll_method = f'swipe_{swipe_dir}'
                            method_found = True
                            print(
                                f"  ✅ swipe {swipe_dir} 方式有效！发现新内容（元素+{test_new_elements}, 航班+{test_new_flights}）")
                            print(f"  📌 将使用方式: swipe {swipe_dir}")
                        else:
                            print(f"  ❌ swipe {swipe_dir} 方式未发现新内容")
                    except Exception as e:

                        print(f"  ⚠️ 测试swipe {swipe_dir}方式时出错: {e}")
                
                # 即使没有找到有效方式，如果还在最小滚动次数内，也强制继续滚动（使用swipe down）
                if not method_found and initial_scrolls < min_scrolls:
                    print(
                        f"⚠️ 未找到有效滚动方式，但仍在最小滚动次数内（{initial_scrolls}/{min_scrolls}），强制继续向下滚动...")
                    # 尝试向下滚动以加载更多内容
                    perform_scroll_swipe(
                        driver, scrollable_info, direction='down')
                    time.sleep(3.0)
                    max_scrolls -= 1
                    continue
                
                # 如果所有方式都测试过且都无效，且已经达到最小滚动次数，结束滚动
                if not method_found:
                    if initial_scrolls >= min_scrolls:
                        print("❌ 所有滚动方式都无效，未发现新内容，结束滚动")
                        break
                    else:
                        # 继续尝试向下滚动以加载更多内容
                        print(
                            f"📌 继续向下滚动（最小滚动次数: {initial_scrolls}/{min_scrolls}）...")
                        perform_scroll_swipe(
                            driver, scrollable_info, direction='down')
                        time.sleep(3.0)
                        max_scrolls -= 1
                        continue
                else:
                    # 找到了有效方式，继续下一轮滚动
                    max_scrolls -= 1
                    continue
        else:
            # 有有效方式，继续使用
            # 注意：滚动已经在循环开始处执行了，这里只需要处理逻辑判断
            if has_new_content:
                # 有新内容，重置稳定计数，继续下一轮（滚动已在循环开始处执行）
                stable_count = 0
                max_scrolls -= 1
                continue
            else:
                # 没有新内容
                stable_count += 1
                print(f"⚠️ 未发现新内容，稳定计数: {stable_count}")
                
                # 如果还在最小滚动次数内，强制继续滚动（即使没有检测到新内容）
                if initial_scrolls < min_scrolls:
                    print(
                        f"📌 仍在最小滚动次数内（{initial_scrolls}/{min_scrolls}），继续向下滚动...")
                    # 滚动已在循环开始处执行，这里只需要继续
                    max_scrolls -= 1
                    continue
                
                # 如果稳定计数达到阈值（连续3次无新内容），重新测试所有滚动方式
                if stable_count >= 3:
                    print("🔄 当前滚动方式无新内容，重新测试所有滚动方式...")
                    effective_scroll_method = None  # 重置有效方式
                    stable_count = 0  # 重置稳定计数
                    continue
                else:
                    # 尝试大幅度滚动（统一使用向下滚动以加载更多内容）
                    print(f"🔄 尝试大幅度向下滚动...")
                    perform_scroll_swipe(
                        driver, scrollable_info, direction='down')
                    time.sleep(3.0)
                    max_scrolls -= 1
                    continue
        
        max_scrolls -= 1
    
    print(
        f"🏁 滚动完成，总共滚动 {scroll_count} 次，总元素数: {len(all_elements_text)}, 唯一航班: {len(unique_flights)}")
    if effective_scroll_method:
        print(f"📌 最终使用的有效滚动方式: {effective_scroll_method}")
    
    # 最后滚动回顶部以便完整查看和提取
    print("📍 滚动回页面顶部以便完整提取所有内容...")
    scroll_to_top(driver)
    
    # 等待页面稳定
    time.sleep(2)
    
    # 获取最终页面源码
    try:
        page_source = driver.page_source
        # 最终提取时也读取全部可见内容，不限制bounds
        final_flights, _, final_element_count = extract_flight_elements_from_xml(
            page_source, driver=None)
        print(
            f"✅ 最终页面源码长度: {len(page_source)} 字符，元素数: {final_element_count}, 唯一航班: {len(final_flights)}")
    except Exception as e:

        print(f"⚠️ 获取最终页面源码失败: {e}")
        page_source = ""
    
    # 保存页面源码
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    fp = os.path.join(output_dir, f"flight_page_source_{ts}.xml")
    try:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"💾 页面源码已保存到: {fp}")
    except Exception as e:

        print(f"⚠️ 保存页面源码失败: {e}")
        fp = None
    
    return page_source, fp



