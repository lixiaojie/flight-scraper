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
from city_selection import step4a_select_from_city, step4b_select_to_city, get_current_page_settings
from date_selection import step4c_select_date

def launch_12306_app(driver):
    """启动12306应用"""
    print("📱 启动12306应用...")
    
    try:
        # 终止应用（如果正在运行）
        try:
            driver.terminate_app("com.MobileTicket")
            print("✅ 已终止现有12306应用")
            time.sleep(2)
        except Exception as e:

            print(f"⚠️ 终止应用时出错: {e}")
        
        # 检查是否回到主屏幕
        try:
            home_screen_indicators = [
                "com.android.launcher3",
                "com.android.launcher", 
                "com.google.android.apps.nexuslauncher",
                "com.miui.home"
            ]
            
            current_activity = driver.current_activity
            print(f"📱 当前Activity: {current_activity}")
            
            is_home_screen = any(
                indicator in current_activity for indicator in home_screen_indicators)
            
            if not is_home_screen:
                print("⚠️ 未检测到主屏幕，尝试按Home键...")
                driver.press_keycode(3)  # Home键
                time.sleep(1)
        except Exception as e:

            print(f"⚠️ 检查主屏幕状态时出错: {e}")
        
        # 启动12306应用
        print("🚀 启动12306应用...")
        driver.activate_app("com.MobileTicket")
        print("✅ 12306应用已启动")
        time.sleep(3)  # 等待应用完全加载
        
        return True
        
    except Exception as e:


        print(f"❌ 启动12306应用失败: {e}")
        return False



def step2_check_homepage(driver):
    """步骤2: 检查主页面（含重试/广告处理）"""
    print("\n🏠 步骤2: 检查主页面（含重试/广告处理）")

    max_attempts = 6  # 增加重试次数，覆盖首次冷启动广告/引导页
    for attempt in range(1, max_attempts + 1):
        try:
            # 优先尝试关闭可能的广告或引导弹窗
            try:
                for acc_id in [
                    "跳过", "关闭", "以后再说", "我知道了", "同意并继续"
                ]:
                    els = driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().text("{acc_id}")')
                    if els:
                        els[0].click()
                        print(f"🧹 关闭了弹窗: {acc_id}")
                        wait_step(driver, 1)
                        break
            except Exception:

                pass

            # 检查主页面容器
            home_container = driver.find_element(
                AppiumBy.ID, "com.MobileTicket:id/ticket_home_content_container")
            print("✅ 主页面容器已找到")
            wait_step(driver)
            return True

        except NoSuchElementException:


            print(f"⚠️ 第{attempt}/{max_attempts}次：主页面未就绪，等待后重试…")
            wait_step(driver, 2)
            continue
        except Exception as e:


            print(f"❌ 检查主页面失败: {e}")
            wait_step(driver, 2)
            continue

    print("❌ 多次尝试仍未进入主页面")
    return False



def step3_click_air_rail_transfer(driver):
    """步骤3: 点击空铁联运按钮（带循环重试）"""
    print("\n🚄 步骤3: 点击空铁联运按钮")
    
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        print(f"🔄 尝试 {attempt}/{max_attempts}")
        
        try:
            # 点击空铁联运按钮
            air_rail_button = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID, "空铁联运")
            air_rail_button.click()
            print("✅ 空铁联运按钮已点击")
            
            wait_step(driver)
            return True
            
        except NoSuchElementException:

            print(f"⚠️ 第{attempt}次尝试：空铁联运按钮未找到")
            
            if attempt < max_attempts:
                print("🔄 退回到步骤2，重新检查主页面...")
                # 退回到步骤2
                if not step2_check_homepage(driver):
                    print("❌ 主页面检查失败")
                    return False
                wait_step(driver, 2)  # 等待2秒后重试
            else:
                print("❌ 5次尝试后仍未找到空铁联运按钮")
                return False
                
        except Exception as e:

            print(f"❌ 第{attempt}次尝试失败: {e}")
            if attempt >= max_attempts:
                return False
            wait_step(driver, 2)
    
    return False



def step4_check_air_rail_page(driver):
    """步骤4: 检查空铁联运页面或航班动态选项"""
    print("\n✈️ 步骤4: 检查空铁联运页面或航班动态选项")
    
    try:
        # 首先尝试检查空铁联运首页
        try:
            air_rail_page = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                                               'new UiSelector().text("空铁联运首页")')
            print("✅ 空铁联运首页已找到")
            wait_step(driver)
            return True
        except NoSuchElementException:

            print("⚠️ 空铁联运首页未找到，尝试查找航班动态选项...")
        
        # 如果空铁联运首页未找到，尝试查找航班动态选项
        try:
            flight_dynamic = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                                               'new UiSelector().text("航班动态")')
            print("✅ 航班动态选项已找到")
            wait_step(driver)
            return True
        except NoSuchElementException:

            print("❌ 航班动态选项也未找到")
            return False
            
    except Exception as e:


        print(f"❌ 检查页面失败: {e}")
        return False



def step5_click_search(driver):
    """步骤5: 点击查询按钮（带页面刷新）"""
    print("\n🔍 步骤5: 点击查询按钮")
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"🔄 尝试 {attempt}/{max_attempts}")
        
        try:
            # 点击查询按钮
            search_button = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                              'new UiSelector().text("查询")')
            search_button.click()
            print("✅ 查询按钮已点击")
            
            wait_step(driver)
            return True
            
        except NoSuchElementException:

            print(f"⚠️ 第{attempt}次尝试：查询按钮未找到")
            
            if attempt < max_attempts:
                print("🔄 刷新当前页面...")
                try:
                    # 刷新页面
                    driver.refresh()
                    print("✅ 页面已刷新")
                    wait_step(driver, 2)  # 等待2秒让页面加载
                except Exception as e:

                    print(f"⚠️ 页面刷新失败: {e}")
                    # 尝试其他刷新方法
                    try:
                        driver.back()
                        wait_step(driver, 1)
                        driver.forward()
                        print("✅ 使用前进后退刷新页面")
                    except Exception as e2:

                        print(f"⚠️ 前进后退刷新也失败: {e2}")
            else:
                print("❌ 3次尝试后仍未找到查询按钮")
                return False
                
        except Exception as e:


            print(f"❌ 第{attempt}次尝试失败: {e}")
            if attempt >= max_attempts:
                return False
            wait_step(driver, 2)
    
    return False



def step6_check_flight_list(driver):
    """步骤6: 检查航班列表页面并设置价格排序"""
    print("\n📋 步骤6: 检查航班列表页面")
    
    try:
        # 检查航班列表页面
        flight_list = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                        'new UiSelector().text("航班列表")')
        print("✅ 航班列表页面已找到")
        
        # 点击价格排序按钮
        print("🔄 设置价格排序（从低到高）...")
        try:
            price_button = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                             'new UiSelector().text("价格")')
            price_button.click()
            print("✅ 价格排序按钮已点击")
            time.sleep(2)
            
            # 检查是否切换为"价格 低-高"
            try:
                price_sorted = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                                                 'new UiSelector().text("价格 低-高")')
                print("✅ 价格排序已设置为从低到高")
            except BaseException:

                print("⚠️ 价格排序状态未确认，继续执行")
                
        except Exception as e:


            print(f"⚠️ 价格排序设置失败: {e}，继续执行")
        
        # 航司筛选步骤
        print("🔄 执行航司筛选...")
        airline_not_found_warning = None
        try:
            # 只有当环境变量明确设置时才进行筛选，默认为空（不筛选）
            airline = os.getenv('SCRAPER_AIRLINE', '')
            if airline and airline != '全部' and airline.strip():
                print(f"🎯 筛选航空公司: {airline}")
                
                # 点击筛选按钮
                try:
                    filter_button = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("筛选")')
                    filter_button.click()
                    print("✅ 筛选按钮已点击")
                    time.sleep(2)
                    
                    # 在筛选浮层中选择目标航空公司
                    try:
                        airline_element = driver.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{airline}")')
                        airline_element.click()
                        print(f"✅ 已选择航空公司: {airline}")
                        time.sleep(1)
                        
                        # 点击确认按钮
                        try:
                            confirm_button = driver.find_element(
                                AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("确认")')
                            confirm_button.click()
                            print("✅ 筛选确认已点击")
                            time.sleep(2)
                        except BaseException:

                            print("⚠️ 筛选确认按钮未找到，尝试其他确认方式")
                            # 尝试点击空白区域关闭筛选浮层
                            driver.tap([(500, 800)], 100)
                            time.sleep(1)
                            
                    except NoSuchElementException:


                        # 指定的航空公司在筛选菜单中未找到
                        airline_not_found_warning = f"⚠️ 指定的航空公司 '{airline}' 在筛选菜单中未找到，将返回全量结果。请更换日期或指定其他航空公司。"
                        tprint(airline_not_found_warning)
                        
                        # 关闭筛选浮层
                        try:
                            # 尝试点击取消或返回按钮
                            try:
                                cancel_button = driver.find_element(
                                    AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("取消")')
                                cancel_button.click()
                                print("✅ 已点击取消按钮关闭筛选浮层")
                                time.sleep(1)
                            except BaseException:

                                # 尝试点击返回按钮
                                try:
                                    back_button = driver.find_element(
                                        AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("返回")')
                                    back_button.click()
                                    print("✅ 已点击返回按钮关闭筛选浮层")
                                    time.sleep(1)
                                except BaseException:

                                    # 最后尝试点击空白区域关闭筛选浮层
                                    driver.tap([(500, 800)], 100)
                                    print("✅ 已通过点击空白区域关闭筛选浮层")
                                    time.sleep(1)
                        except Exception as close_error:


                            print(f"⚠️ 关闭筛选浮层时出错: {close_error}，尝试点击空白区域")
                            driver.tap([(500, 800)], 100)
                            time.sleep(1)
                        
                    except Exception as e:


                        print(f"⚠️ 选择航空公司失败: {e}")
                        
                except Exception as e:


                    print(f"⚠️ 筛选按钮未找到: {e}")
            else:
                print("ℹ️ 未指定航空公司或选择全部，跳过航司筛选")
                
        except Exception as e:


            print(f"⚠️ 航司筛选步骤失败: {e}，继续执行")
        
        # 如果指定的航空公司未找到，尝试更新任务记录的notes字段
        if airline_not_found_warning:
            try:
                task_id = os.getenv('TASK_ID')
                if task_id:
                    api_base_url = os.getenv(
                        'API_BASE_URL', 'http://localhost:8000')
                    import requests
                    try:
                        # 尝试更新任务记录的notes字段
                        response = requests.put(
                            f"{api_base_url}/api/tasks/{task_id}/notes",
                            json={"notes": airline_not_found_warning},
                            timeout=5
                        )
                        if response.status_code == 200:
                            print("✅ 已将航空公司未找到的警告信息保存到任务记录")
                        else:
                            print(
                                f"⚠️ 更新任务记录notes字段失败: {response.status_code}")
                    except Exception as api_error:

                        print(f"⚠️ 更新任务记录notes字段时出错: {api_error}")
            except Exception as update_error:


                print(f"⚠️ 尝试更新任务记录时出错: {update_error}")
        
        wait_step(driver)
        return True
        
    except NoSuchElementException:


        print("❌ 航班列表页面未找到")
        return False
    except Exception as e:


        print(f"❌ 检查航班列表失败: {e}")
        return False



def navigate_and_search(driver, from_city, to_city, depart_date):
    """根据输入进行完整的导航和查询流程"""
    print(
        f"\n🔍 navigate_and_search 接收参数: 出发城市={from_city}, 到达城市={to_city}, 出发日期={depart_date}")
    # 首先启动12306应用
    if not launch_12306_app(driver):
        print("❌ 无法启动12306应用，退出")
        return False

    # 执行完整的抓取步骤
    # 先检查当前页面设置，如果城市和日期都已正确，可以跳过选择步骤
    current_settings = get_current_page_settings(driver)
    current_from_city = current_settings.get('from_city')
    current_to_city = current_settings.get('to_city')
    current_date = current_settings.get('depart_date')
    
    # 检查是否需要修改城市或日期
    need_change_from = current_from_city != from_city if from_city else False
    need_change_to = current_to_city != to_city if to_city else False
    need_change_date = current_date != depart_date if depart_date else False
    
    if not need_change_from and not need_change_to and not need_change_date:
        print("✅ 当前页面设置已与目标一致，跳过城市和日期选择步骤")
    else:
        if need_change_from:
            print(f"🔄 需要修改出发城市: {current_from_city} → {from_city}")
        if need_change_to:
            print(f"🔄 需要修改到达城市: {current_to_city} → {to_city}")
        if need_change_date:
            print(f"🔄 需要修改出发日期: {current_date} → {depart_date}")
    
    steps = [
        lambda: step2_check_homepage(driver),
        lambda: step3_click_air_rail_transfer(driver),
        lambda: step4_check_air_rail_page(driver),
        lambda: step4a_select_from_city(driver, from_city) if need_change_from else (print("⏭️ 跳过出发城市选择（已正确）") or True),  # 仅在需要时选择
        lambda: step4b_select_to_city(driver, to_city) if need_change_to else (print("⏭️ 跳过到达城市选择（已正确）") or True),      # 仅在需要时选择
        lambda: step4c_select_date(driver, depart_date) if need_change_date else (print("⏭️ 跳过日期选择（已正确）") or True),  # 仅在需要时选择
        lambda: step5_click_search(driver),
        lambda: step6_check_flight_list(driver)
    ]
    
    for i, step in enumerate(steps, 2):
        if not step():
            print(f"❌ 步骤{i}失败，抓取流程中断")
            return False
    
    print("✅ 所有导航步骤完成")
    return True


# ==================== 城市选择功能 ====================


