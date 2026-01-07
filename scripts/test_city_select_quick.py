#!/usr/bin/env python3
"""
快速验证城市查找和选择功能
用于调试城市选择页面的查找和选择逻辑
"""
import os
import sys
import time

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.common.exceptions import NoSuchElementException
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已安装appium和selenium")
    sys.exit(1)

from city_selection import (
    find_city_search_box,
    input_city_search,
    select_city_from_results,
    _clean_city_name
)
from utils import wait_step


def test_city_find_and_select():
    """快速测试城市查找和选择功能"""
    print("=" * 80)
    print("城市查找和选择功能快速验证")
    print("=" * 80)
    
    # 使用与主脚本相同的配置方式
    import os
    
    # 从环境变量或配置文件获取配置
    target_udid = os.getenv("SCRAPER_DEVICE_UDID", "emulator-5554")
    appium_server_url = os.getenv("APPIUM_SERVER_URL", "http://appium:4723")
    
    # 配置Appium选项（与主脚本保持一致）
    caps = {
        'platformName': 'Android',
        'appium:automationName': 'UiAutomator2',
        "appium:remoteAdbHost": "host.docker.internal",
        "appium:remoteAdbPort": "5037",
        'appium:deviceName': 'Android Emulator',
        'appium:platformVersion': '16',
        'appium:noReset': True,
        'appium:fullReset': False,
        'appium:autoGrantPermissions': True,
        'appium:newCommandTimeout': 300,
        'appium:adbExecTimeout': 120000,
    }
    
    # 设置UDID
    if target_udid:
        caps['appium:udid'] = target_udid
    
    options = UiAutomator2Options().load_capabilities(caps)
    
    print(f"\n🔗 连接到Appium服务器: {appium_server_url}")
    print(f"📱 目标设备UDID: {target_udid}")
    
    try:
        driver = webdriver.Remote(appium_server_url, options=options)
        print("✅ 已连接到设备")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("1. Appium服务器正在运行")
        print("2. 模拟器已启动并连接")
        print("3. 设备已停留在城市选择页面")
        return
    
    try:
        # 等待应用稳定
        print("\n⏳ 等待应用稳定...")
        time.sleep(2)
        
        # 检查当前页面
        print("\n🔍 检查当前页面...")
        try:
            page_source = driver.page_source
            if "搜索" in page_source or "请输入" in page_source or "城市" in page_source:
                print("✅ 当前在城市选择页面")
            else:
                print("⚠️ 当前可能不在城市选择页面")
                print("页面内容预览:")
                print(page_source[:200])
        except Exception as e:
            print(f"⚠️ 检查页面失败: {e}")
        
        # 测试城市名称（可以从命令行参数获取，或使用默认值）
        test_city = sys.argv[1] if len(sys.argv) > 1 else "济南"
        print(f"\n🧪 测试城市: {test_city}")
        print("-" * 80)
        
        # 步骤1: 清理城市名称
        print("\n步骤1: 清理城市名称")
        cleaned_city = _clean_city_name(test_city)
        print(f"  原始: '{test_city}'")
        print(f"  清理后: '{cleaned_city}'")
        
        # 步骤2: 查找搜索框
        print("\n步骤2: 查找搜索框")
        search_box = find_city_search_box(driver)
        if not search_box:
            print("❌ 未找到搜索框")
            return
        print("✅ 搜索框已找到")
        
        # 步骤3: 测试输入
        print(f"\n步骤3: 输入城市名称 '{cleaned_city}'")
        result = input_city_search(driver, test_city)
        if not result:
            print("❌ 输入失败")
            return
        print("✅ 输入成功")
        
        # 步骤4: 等待搜索结果
        print("\n步骤4: 等待搜索结果出现...")
        time.sleep(2)
        
        # 步骤5: 检查搜索结果
        print("\n步骤5: 检查搜索结果")
        try:
            # 尝试查找包含城市名称的结果
            result_element = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{cleaned_city}")')
            print(f"✅ 找到搜索结果: {result_element.text}")
            
            # 列出所有包含城市名称的结果
            all_results = driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{cleaned_city}")')
            print(f"\n📋 找到 {len(all_results)} 个包含 '{cleaned_city}' 的结果:")
            for i, elem in enumerate(all_results[:10], 1):  # 最多显示10个
                try:
                    print(f"  {i}. {elem.text}")
                except:
                    print(f"  {i}. (无法获取文本)")
            
            # 查找"城市（不限站点）"或类似选项
            print("\n🔍 查找'城市（不限站点）'或类似选项...")
            city_no_site_options = []
            try:
                # 尝试多种可能的文本模式
                patterns = [
                    f'new UiSelector().textContains("{cleaned_city}").textContains("城市").textContains("不限")',
                    f'new UiSelector().textContains("{cleaned_city}").textContains("城市").textContains("站点")',
                    f'new UiSelector().textContains("{cleaned_city}").textContains("不限站点")',
                    f'new UiSelector().textContains("{cleaned_city}").textContains("城市").textContains("(")',
                ]
                
                for pattern in patterns:
                    try:
                        elements = driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR, pattern)
                        for elem in elements:
                            try:
                                text = elem.text
                                if "不限" in text or "站点" in text or "(" in text:
                                    city_no_site_options.append((elem, text))
                                    print(f"  ✅ 找到选项: {text}")
                            except:
                                pass
                    except:
                        pass
                
                # 如果没有找到，尝试在页面源码中搜索
                if not city_no_site_options:
                    try:
                        page_source = driver.page_source
                        import re
                        # 查找包含城市名称和"不限"或"站点"的文本
                        pattern = f'.*{re.escape(cleaned_city)}.*(不限|站点|城市).*'
                        matches = re.findall(pattern, page_source, re.IGNORECASE)
                        if matches:
                            print(f"  ℹ️ 在页面源码中找到相关文本: {matches[:3]}")
                    except:
                        pass
            except Exception as e:
                print(f"  ⚠️ 查找'城市（不限站点）'选项失败: {e}")
        except NoSuchElementException:
            print("⚠️ 未找到搜索结果")
            print("\n当前页面内容预览:")
            try:
                page_source = driver.page_source
                print(page_source[:500])
            except Exception as e:
                print(f"⚠️ 获取页面内容失败: {e}")
        
        # 步骤6: 详细调试选择城市
        print(f"\n步骤6: 详细调试选择城市 '{cleaned_city}'")
        print("-" * 80)
        
        # 6.0: 优先尝试点击"城市（不限站点）"选项
        print("\n6.0 策略0: 尝试点击'城市（不限站点）'选项")
        try:
            # 查找包含城市名称和"不限站点"或类似文本的元素
            city_no_site_element = None
            city_no_site_text = None
            
            # 方法1: 查找包含"不限站点"的文本
            try:
                city_no_site_element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{cleaned_city}").textContains("不限站点")')
                city_no_site_text = city_no_site_element.text
                print(f"✅ 找到'不限站点'选项: {city_no_site_text}")
            except:
                # 方法2: 查找包含"城市"和"不限"的文本
                try:
                    city_no_site_element = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{cleaned_city}").textContains("城市").textContains("不限")')
                    city_no_site_text = city_no_site_element.text
                    print(f"✅ 找到'城市不限'选项: {city_no_site_text}")
                except:
                    # 方法3: 查找包含"城市"和"("的文本（可能是"城市（不限站点）"）
                    try:
                        all_city_elements = driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().textContains("{cleaned_city}").textContains("城市")')
                        for elem in all_city_elements:
                            try:
                                text = elem.text
                                if "(" in text or "不限" in text or "站点" in text:
                                    city_no_site_element = elem
                                    city_no_site_text = text
                                    print(f"✅ 找到可能的'城市（不限站点）'选项: {text}")
                                    break
                            except:
                                pass
                    except:
                        pass
            
            if city_no_site_element and city_no_site_text:
                print(f"   位置: {city_no_site_element.location}")
                print(f"   大小: {city_no_site_element.size}")
                
                # 尝试点击这个元素
                location = city_no_site_element.location
                size = city_no_site_element.size
                center_x = location['x'] + size['width'] // 2
                center_y = location['y'] + size['height'] // 2
                
                print(f"   尝试点击'城市（不限站点）'选项: ({center_x}, {center_y})")
                try:
                    driver.tap([(center_x, center_y)], 100)
                    print("   ✅ tap()成功")
                    time.sleep(3)  # 等待选择生效
                    
                    # 检查是否返回主页面
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（策略0成功）")
                        # 验证城市是否被选择
                        if cleaned_city in page_source:
                            print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                            print("✅ 使用'城市（不限站点）'选项选择成功！")
                            # 如果成功，可以跳过后续策略
                            success = True
                        else:
                            print(f"⚠️ 城市 '{cleaned_city}' 可能未正确选择")
                            success = False
                    else:
                        print("⚠️ 可能还在城市选择页面")
                        success = False
                except Exception as e:
                    print(f"   ❌ tap()失败: {e}")
                    success = False
                
                if success:
                    print("\n✅ 策略0成功，跳过后续策略")
                    # 如果成功，可以跳过后续的6.1-6.3策略
                    skip_other_strategies = True
                else:
                    print("\n⚠️ 策略0未成功，继续尝试其他策略")
                    skip_other_strategies = False
            else:
                print("❌ 未找到'城市（不限站点）'选项")
                skip_other_strategies = False
        except Exception as e:
            print(f"❌ 策略0失败: {e}")
            skip_other_strategies = False
        
        # 如果策略0成功，跳过后续策略
        if 'skip_other_strategies' in locals() and skip_other_strategies:
            pass  # 跳过6.1-6.3
        else:
            # 6.1: 尝试策略1 - 带"城市"标签的结果
            print("\n6.1 策略1: 查找带'城市'标签的结果")
        try:
            # 先关闭键盘（如果打开）
            print("   尝试关闭键盘...")
            try:
                driver.hide_keyboard()
                time.sleep(0.5)
            except:
                pass
            
            city_element = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{cleaned_city}").textContains("城市")')
            print(f"✅ 找到元素: {city_element.text}")
            print(f"   位置: {city_element.location}")
            print(f"   大小: {city_element.size}")
            
            # 检查元素是否可见和可点击
            try:
                is_displayed = city_element.is_displayed()
                is_enabled = city_element.is_enabled()
                print(f"   可见: {is_displayed}, 启用: {is_enabled}")
            except:
                pass
            
            # 滚动到元素可见
            try:
                print("   滚动到元素可见...")
                driver.execute_script("mobile: scroll", {
                    "strategy": "accessibility id",
                    "selector": city_element.text,
                    "toVisible": "true"
                })
                time.sleep(0.5)
            except:
                try:
                    # 备用滚动方法
                    location = city_element.location
                    size = city_element.size
                    center_y = location['y'] + size['height'] // 2
                    screen_size = driver.get_window_size()
                    if center_y > screen_size['height'] * 0.8:
                        # 元素在屏幕下方，向上滚动
                        driver.swipe(
                            screen_size['width'] // 2,
                            screen_size['height'] * 0.8,
                            screen_size['width'] // 2,
                            screen_size['height'] * 0.2,
                            500
                        )
                        time.sleep(0.5)
                except:
                    pass
            
            # 尝试多种点击方法
            location = city_element.location
            size = city_element.size
            center_x = location['x'] + size['width'] // 2
            center_y = location['y'] + size['height'] // 2
            left_x = location['x'] + size['width'] * 0.2  # 左侧20%位置
            right_x = location['x'] + size['width'] * 0.8  # 右侧80%位置
            text_start_x = location['x'] + 10  # 文本开始位置（左侧10像素）
            
            # 打印页面源码片段用于调试
            try:
                page_source = driver.page_source
                # 查找包含城市名称的XML片段
                import re
                pattern = f'.*{re.escape(cleaned_city)}.*'
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    print(f"   📄 页面源码片段（包含'{cleaned_city}'）:")
                    for match in matches[:3]:  # 只显示前3个匹配
                        print(f"      {match[:200]}")
            except:
                pass
            
            success = False
            
            # 方法1: 短tap点击中心
            print(f"   方法1: tap点击中心 ({center_x}, {center_y})")
            try:
                driver.tap([(center_x, center_y)], 100)
                print("   ✅ tap()成功")
                time.sleep(2)
                page_source = driver.page_source
                if "查询" in page_source or "出发" in page_source:
                    print("✅ 已返回到主页面（方法1成功）")
                    success = True
            except Exception as e:
                print(f"   ❌ tap()失败: {e}")
            
            if not success:
                # 方法2: 长按（300ms）
                print(f"   方法2: 长按中心 ({center_x}, {center_y})")
                try:
                    driver.tap([(center_x, center_y)], 300)
                    print("   ✅ 长按成功")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法2成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ 长按失败: {e}")
            
            if not success:
                # 方法3: 点击文本开始位置（左侧）
                print(f"   方法3: tap点击文本开始位置 ({int(text_start_x)}, {center_y})")
                try:
                    driver.tap([(int(text_start_x), int(center_y))], 100)
                    print("   ✅ 文本位置点击成功")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法3成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ 文本位置点击失败: {e}")
            
            if not success:
                # 方法3b: 点击左侧20%位置
                print(f"   方法3b: tap点击左侧 ({int(left_x)}, {center_y})")
                try:
                    driver.tap([(int(left_x), int(center_y))], 100)
                    print("   ✅ 左侧点击成功")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法3b成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ 左侧点击失败: {e}")
            
            if not success:
                # 方法4: 使用Actions API点击
                print(f"   方法4: 使用Actions API点击")
                try:
                    from appium.webdriver.common.touch_action import TouchAction
                    action = TouchAction(driver)
                    action.tap(x=int(center_x), y=int(center_y)).perform()
                    print("   ✅ Actions API点击成功")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法4成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ Actions API点击失败: {e}")
            
            if not success:
                # 方法5: 使用click()方法
                print(f"   方法5: 使用click()方法")
                try:
                    city_element.click()
                    print("   ✅ click()成功")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法5成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ click()失败: {e}")
            
            if not success:
                # 方法6: 双击
                print(f"   方法6: 双击中心")
                try:
                    driver.tap([(center_x, center_y)], 100)
                    time.sleep(0.2)
                    driver.tap([(center_x, center_y)], 100)
                    print("   ✅ 双击完成")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法6成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ 双击失败: {e}")
            
            if not success:
                # 方法7: 尝试查找父元素并点击
                print(f"   方法7: 查找父元素并点击")
                try:
                    # 尝试通过XPath查找父元素
                    from lxml import etree
                    page_source = driver.page_source
                    root = etree.fromstring(page_source.encode('utf-8'))
                    xpath_query = f'.//*[contains(@text, "{cleaned_city}") and contains(@text, "城市")]'
                    elements = root.xpath(xpath_query)
                    if elements:
                        elem = elements[0]
                        # 尝试获取bounds属性
                        bounds = elem.get('bounds', '')
                        if bounds:
                            import re
                            match = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                            if match:
                                x1, y1, x2, y2 = map(int, match.groups())
                                parent_center_x = (x1 + x2) // 2
                                parent_center_y = (y1 + y2) // 2
                                print(f"   父元素中心: ({parent_center_x}, {parent_center_y})")
                                driver.tap([(parent_center_x, parent_center_y)], 100)
                                print("   ✅ 父元素点击成功")
                                time.sleep(2)
                                page_source = driver.page_source
                                if "查询" in page_source or "出发" in page_source:
                                    print("✅ 已返回到主页面（方法7成功）")
                                    success = True
                except Exception as e:
                    print(f"   ❌ 父元素点击失败: {e}")
            
            if not success:
                # 方法8: 多次点击
                print(f"   方法8: 多次tap点击（3次）")
                try:
                    for i in range(3):
                        driver.tap([(center_x, center_y)], 100)
                        time.sleep(0.3)
                    print("   ✅ 多次点击完成")
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面（方法8成功）")
                        success = True
                except Exception as e:
                    print(f"   ❌ 多次点击失败: {e}")
            
            # 最终检查
            if success:
                # 验证城市是否被选择
                time.sleep(1)  # 额外等待
                page_source = driver.page_source
                if cleaned_city in page_source:
                    print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                else:
                    print(f"⚠️ 城市 '{cleaned_city}' 可能未正确选择")
                    print("   当前页面内容预览:")
                    print(page_source[:500])
            else:
                print("❌ 所有点击方法都失败")
                print("   🔍 尝试分析原因...")
                
                # 检查元素是否仍然存在
                try:
                    city_element_check = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{cleaned_city}").textContains("城市")')
                    print("   ✅ 元素仍然存在")
                except:
                    print("   ⚠️ 元素已不存在（可能已被点击但未返回）")
                
                # 尝试按返回键
                print("   尝试按返回键...")
                try:
                    driver.back()
                    time.sleep(2)
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 通过返回键返回到主页面")
                        # 检查城市是否被选择
                        if cleaned_city in page_source:
                            print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                        else:
                            print(f"⚠️ 城市 '{cleaned_city}' 未在主页面中找到")
                    else:
                        print("❌ 返回键也未生效")
                        print("   当前页面内容预览:")
                        print(page_source[:500])
                        print("\n   📋 建议:")
                        print("   1. 检查元素是否被其他元素遮挡")
                        print("   2. 检查是否需要特殊的点击手势")
                        print("   3. 检查页面是否需要额外的确认操作")
                except Exception as e:
                    print(f"❌ 返回键失败: {e}")
        except NoSuchElementException:
            print("❌ 未找到带'城市'标签的结果")
        
        # 6.2: 尝试策略2 - 精确匹配
        print("\n6.2 策略2: 精确匹配")
        try:
            city_element = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{cleaned_city}")')
            print(f"✅ 找到元素: {city_element.text}")
            print(f"   位置: {city_element.location}")
            print(f"   大小: {city_element.size}")
            
            # 优先使用tap点击
            try:
                location = city_element.location
                size = city_element.size
                center_x = location['x'] + size['width'] // 2
                center_y = location['y'] + size['height'] // 2
                print(f"   使用tap点击: ({center_x}, {center_y})")
                driver.tap([(center_x, center_y)], 100)
                print("✅ tap()成功")
                time.sleep(3)  # 增加等待时间
                
                # 检查是否返回主页面
                page_source = driver.page_source
                if "查询" in page_source or "出发" in page_source:
                    print("✅ 已返回到主页面（策略2成功）")
                    if cleaned_city in page_source:
                        print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                else:
                    print("⚠️ 可能还在城市选择页面")
            except Exception as e:
                print(f"❌ tap()失败: {e}")
                # 尝试click作为备用
                try:
                    city_element.click()
                    print("✅ click()成功（备用方法）")
                    time.sleep(3)
                except Exception as e2:
                    print(f"❌ click()也失败: {e2}")
        except NoSuchElementException:
            print("❌ 未找到精确匹配的结果")
        
        # 6.3: 尝试策略3 - textContains
        print("\n6.3 策略3: textContains")
        try:
            city_element = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{cleaned_city}")')
            print(f"✅ 找到元素: {city_element.text}")
            print(f"   位置: {city_element.location}")
            print(f"   大小: {city_element.size}")
            
            # 优先使用tap点击
            try:
                location = city_element.location
                size = city_element.size
                center_x = location['x'] + size['width'] // 2
                center_y = location['y'] + size['height'] // 2
                print(f"   使用tap点击: ({center_x}, {center_y})")
                driver.tap([(center_x, center_y)], 100)
                print("✅ tap()成功")
                time.sleep(3)  # 增加等待时间
                
                # 检查是否返回主页面
                page_source = driver.page_source
                if "查询" in page_source or "出发" in page_source:
                    print("✅ 已返回到主页面（策略3成功）")
                    if cleaned_city in page_source:
                        print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                else:
                    print("⚠️ 可能还在城市选择页面")
            except Exception as e:
                print(f"❌ tap()失败: {e}")
                # 尝试click作为备用
                try:
                    city_element.click()
                    print("✅ click()成功（备用方法）")
                    time.sleep(3)
                except Exception as e2:
                    print(f"❌ click()也失败: {e2}")
        except NoSuchElementException:
            print("❌ 未找到textContains的结果")
        
        # 6.4: 检查最终状态
        print("\n6.4 检查最终状态")
        time.sleep(1)
        try:
            page_source = driver.page_source
            if "查询" in page_source or "出发" in page_source:
                print("✅ 已返回到主页面")
            elif "搜索" in page_source or "请输入" in page_source:
                print("⚠️ 还在城市选择页面")
            else:
                print("⚠️ 页面状态未知")
        except:
            pass
        
        # 6.5: 使用原始函数测试（如果前面的方法都失败）
        print(f"\n6.5 使用select_city_from_results函数测试")
        
        # 先检查当前页面状态
        try:
            page_source = driver.page_source
            if "查询" in page_source or "出发" in page_source:
                print("   ℹ️ 当前已在主页面")
                print(f"   🔍 检查城市 '{cleaned_city}' 是否在主页面中...")
                if cleaned_city in page_source:
                    print(f"   ✅ 城市 '{cleaned_city}' 已在主页面中，选择成功！")
                    print("   ✅ 测试完成，城市已成功选择并返回主页面")
                else:
                    print(f"   ⚠️ 城市 '{cleaned_city}' 未在主页面中找到")
                    print("   ⚠️ 虽然返回了主页面，但城市可能未正确选择")
            else:
                print("   ℹ️ 当前还在城市选择页面，使用select_city_from_results函数...")
                print("   ⚠️ 前面的所有点击方法都未成功，尝试使用select_city_from_results...")
                select_result = select_city_from_results(driver, test_city)
                if select_result:
                    print("✅ select_city_from_results返回成功")
                    time.sleep(3)
                    # 再次验证
                    page_source = driver.page_source
                    if "查询" in page_source or "出发" in page_source:
                        print("✅ 已返回到主页面")
                        if cleaned_city in page_source:
                            print(f"✅ 城市 '{cleaned_city}' 已成功选择并带回")
                        else:
                            print(f"⚠️ 城市 '{cleaned_city}' 未在主页面中找到")
                    else:
                        print("⚠️ 仍未返回主页面")
                        print("   当前页面内容预览:")
                        print(page_source[:500])
                else:
                    print("❌ select_city_from_results返回失败")
                    print("   ⚠️ 所有方法都失败，可能需要手动检查")
        except Exception as e:
            print(f"⚠️ 检查页面状态失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n按Enter键关闭连接...")
        input()
        try:
            driver.quit()
            print("✅ 连接已关闭")
        except:
            pass


if __name__ == "__main__":
    test_city_find_and_select()

