#!/usr/bin/env python3
"""
12306航班信息抓取自动化脚本
使用Appium自动化Android应用，抓取航班信息
"""

import time
import re
import os
import sys
import requests
import json
from datetime import datetime
from lxml import etree
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FlightScraper12306:
    def __init__(self):
        """初始化航班抓取器"""
        self.driver = None
        self.wait = None
        # 结果输出目录，默认保存到项目的 results 目录，可通过环境变量覆盖
        self.output_dir = os.getenv("SCRAPER_OUTPUT_DIR", os.path.join(os.getcwd(), "results"))
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception:
            # 如果无法创建，降级为当前目录
            self.output_dir = os.getcwd()
        # 可选外部参数（来自环境）
        self.from_city = os.getenv("SCRAPER_FROM_CITY", "")
        self.to_city = os.getenv("SCRAPER_TO_CITY", "")
        # 期望格式: YYYY-MM-DD
        self.depart_date = os.getenv("SCRAPER_DEPART_DATE", "")
        # API基础URL，用于更新任务状态
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.task_id = None
        
    def setup_driver(self):
        """设置Appium驱动"""
        print("🚀 初始化Appium驱动...")
        
        # 连接配置
        desired_caps = {
            'platformName': 'Android',
            'appium:automationName': 'UiAutomator2',
            'appium:deviceName': 'Android Emulator',
            'appium:platformVersion': '16',
            'appium:noReset': True,
            'appium:fullReset': False,
            'appium:autoGrantPermissions': True,
            'appium:newCommandTimeout': 300
        }
        
        try:
            # 创建驱动（Appium Python Client 3.x 推荐写法）
            from appium.options.android import UiAutomator2Options

            target_udid = os.getenv("SCRAPER_DEVICE_UDID")
            caps = {
                'platformName': 'Android',
                'appium:automationName': 'UiAutomator2',
                'appium:deviceName': 'Android Emulator',
                'appium:platformVersion': '16',
                'appium:noReset': True,
                'appium:fullReset': False,
                'appium:autoGrantPermissions': True,
                'appium:newCommandTimeout': 300,
                'appium:adbExecTimeout': 120000,
            }
            if target_udid:
                caps['appium:udid'] = target_udid
            options = UiAutomator2Options().load_capabilities(caps)

            server_url = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
            self.driver = webdriver.Remote(server_url, options=options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Appium驱动初始化成功")
            return True
        except Exception as e:
            print(f"❌ 驱动初始化失败: {e}")
            return False
    
    def wait_step(self, seconds=2):
        """步骤间等待"""
        print(f"⏳ 等待 {seconds} 秒...")
        time.sleep(seconds)
    
    def update_task_status(self, step_name, status="running"):
        """更新任务状态"""
        if not self.task_id:
            return
        
        try:
            url = f"{self.api_base_url}/api/tasks/{self.task_id}/status"
            data = {
                "current_step": step_name,
                "status": status
            }
            response = requests.patch(url, json=data, timeout=5)
            if response.status_code == 200:
                print(f"✅ 任务状态已更新: {step_name}")
            else:
                print(f"⚠️ 状态更新失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 更新任务状态时出错: {e}")
    
    def set_task_id(self, task_id):
        """设置任务ID"""
        self.task_id = task_id
        print(f"📋 任务ID已设置: {task_id}")
    
    def take_screenshot_and_exit(self, reason):
        """截图并退出"""
        print(f"\n📸 截图并退出 - 原因: {reason}")
        
        try:
            # 截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = os.path.join(self.output_dir, f"flight_scraper_error_{timestamp}.png")
            self.driver.save_screenshot(screenshot_filename)
            print(f"📸 截图已保存: {screenshot_filename}")
            
            # 保存页面源码
            page_source = self.driver.page_source
            source_filename = os.path.join(self.output_dir, f"flight_scraper_error_{timestamp}.xml")
            with open(source_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"📄 页面源码已保存: {source_filename}")
            
        except Exception as e:
            print(f"⚠️ 截图保存失败: {e}")
        
        print("🔚 脚本结束")
        if self.driver:
            self.driver.quit()
    
    def step1_launch_12306(self):
        """步骤1: 重启12306应用，确保从首页开始"""
        print("\n📱 步骤1: 重启12306应用")
        self.update_task_status("重启12306应用")
        
        try:
            # 先终止应用，确保从首页开始
            print("🔄 终止12306应用...")
            try:
                self.driver.terminate_app("com.MobileTicket")
                print("✅ 应用已终止")
            except Exception as e:
                print(f"⚠️ 终止应用时出错: {e}")
            
            self.wait_step(1)  # 等待1秒
            
            # 重新启动应用
            print("🚀 重新启动12306应用...")
            self.driver.activate_app("com.MobileTicket")
            print("✅ 12306应用已重启")
            
            self.wait_step()
            return True
            
        except Exception as e:
            print(f"❌ 重启12306失败: {e}")
            return False
    
    def step2_check_homepage(self):
        """步骤2: 检查主页面"""
        print("\n🏠 步骤2: 检查主页面（含重试/广告处理）")
        self.update_task_status("检查主页面")

        max_attempts = 6  # 增加重试次数，覆盖首次冷启动广告/引导页
        for attempt in range(1, max_attempts + 1):
            try:
                # 优先尝试关闭可能的广告或引导弹窗
                try:
                    for acc_id in [
                        "跳过", "关闭", "以后再说", "我知道了", "同意并继续"
                    ]:
                        els = self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{acc_id}")')
                        if els:
                            els[0].click()
                            print(f"🧹 关闭了弹窗: {acc_id}")
                            self.wait_step(1)
                            break
                except Exception:
                    pass

                # 检查主页面容器
                home_container = self.driver.find_element(AppiumBy.ID, "com.MobileTicket:id/ticket_home_content_container")
                print("✅ 主页面容器已找到")
                self.wait_step()
                return True

            except NoSuchElementException:
                print(f"⚠️ 第{attempt}/{max_attempts}次：主页面未就绪，等待后重试…")
                self.wait_step(2)
                continue
            except Exception as e:
                print(f"❌ 检查主页面失败: {e}")
                self.wait_step(2)
                continue

        print("❌ 多次尝试仍未进入主页面")
        return False
    
    def step3_click_air_rail_transfer(self):
        """步骤3: 点击空铁联运按钮（带循环重试）"""
        print("\n🚄 步骤3: 点击空铁联运按钮")
        self.update_task_status("点击空铁联运")
        
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 尝试 {attempt}/{max_attempts}")
            
            try:
                # 点击空铁联运按钮
                air_rail_button = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "空铁联运")
                air_rail_button.click()
                print("✅ 空铁联运按钮已点击")
                
                self.wait_step()
                return True
                
            except NoSuchElementException:
                print(f"⚠️ 第{attempt}次尝试：空铁联运按钮未找到")
                
                if attempt < max_attempts:
                    print("🔄 退回到步骤2，重新检查主页面...")
                    # 退回到步骤2
                    if not self.step2_check_homepage():
                        print("❌ 主页面检查失败")
                        return False
                    self.wait_step(2)  # 等待2秒后重试
                else:
                    print("❌ 5次尝试后仍未找到空铁联运按钮")
                    # 截图并结束
                    self.take_screenshot_and_exit("空铁联运按钮未找到")
                    return False
                    
            except Exception as e:
                print(f"❌ 第{attempt}次尝试失败: {e}")
                if attempt >= max_attempts:
                    self.take_screenshot_and_exit(f"点击空铁联运失败: {e}")
                    return False
                self.wait_step(2)
        
        return False
    
    def step4_check_air_rail_page(self):
        """步骤4: 检查空铁联运页面或航班动态选项"""
        print("\n✈️ 步骤4: 检查空铁联运页面或航班动态选项")
        self.update_task_status("检查空铁联运页面")
        
        try:
            # 首先尝试检查空铁联运首页
            try:
                air_rail_page = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                       'new UiSelector().text("空铁联运首页")')
                print("✅ 空铁联运首页已找到")
                self.wait_step()
                return True
            except NoSuchElementException:
                print("⚠️ 空铁联运首页未找到，尝试查找航班动态选项...")
            
            # 如果空铁联运首页未找到，尝试查找航班动态选项
            try:
                flight_dynamic = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                       'new UiSelector().text("航班动态")')
                print("✅ 航班动态选项已找到")
                self.wait_step()
                return True
            except NoSuchElementException:
                print("❌ 航班动态选项也未找到")
                return False
                
        except Exception as e:
            print(f"❌ 检查页面失败: {e}")
            return False

    def step4a_select_from_city(self):
        """步骤4A: 选择出发城市（占位，后续根据页面结构完善）"""
        if not self.from_city:
            print("ℹ️ 未提供出发城市，跳过选择")
            return True
        print(f"\n🏷️ 步骤4A: 选择出发城市 -> {self.from_city}（占位实现）")
        self.update_task_status("选择出发城市")
        # TODO: 根据页面具体元素完成点击与选择逻辑
        self.wait_step(1)
        return True

    def step4b_select_to_city(self):
        """步骤4B: 选择到达城市（占位，后续根据页面结构完善）"""
        if not self.to_city:
            print("ℹ️ 未提供到达城市，跳过选择")
            return True
        print(f"\n🏷️ 步骤4B: 选择到达城市 -> {self.to_city}（占位实现）")
        self.update_task_status("选择到达城市")
        # TODO: 根据页面具体元素完成点击与选择逻辑
        self.wait_step(1)
        return True

    def step4c_select_date(self):
        """步骤4C: 选择出发日期（根据页面展示文案拼装并点击）
        规则：
        - 先读取当前页面源码，收集可见文本
        - 目标日期若为今天/明天/后天 -> 期望文案为 "M月D日今天|明天|后天"
        - 否则 -> 期望文案为 "M月D日周X"（X=一..日）
        - 在可见文本中匹配优先级：今天/明天/后天 > 周X
        - 找到后使用 exact text 点击；若未找到，退化到按日(instance=0/1)策略
        """
        print("\n📅 步骤4C: 选择出发日期（按展示文案匹配）")
        self.update_task_status("选择出发日期")
        try:
            from datetime import date, datetime as dt, timedelta
            today = date.today()
            weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}

            # 打开日期浮层：优先尝试点击包含"月"且含今日的按钮，如果失败不报错继续
            try:
                current_label = f"{today.month}月{today.day}日{weekday_map[today.weekday()]}"
                btn = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{current_label}")')
                btn.click()
                print(f"✅ 已点击当前日期按钮: {current_label}")
                self.wait_step(1)
            except Exception:
                pass

            if not self.depart_date:
                print("ℹ️ 未提供出发日期，跳过选择")
                return True

            try:
                target = dt.strptime(self.depart_date, "%Y-%m-%d").date()
            except Exception:
                print(f"⚠️ 出发日期格式非法: {self.depart_date}")
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

            # 提取页面文本
            page = self.driver.page_source
            visible_texts = set()
            try:
                root = etree.fromstring(page.encode('utf-8'))
                for el in root.xpath('//*[@text]'):
                    t = el.get('text') or ''
                    if t:
                        visible_texts.add(t)
            except Exception:
                pass

            # 依次尝试候选文案点击
            for label in candidates:
                if label in visible_texts:
                    try:
                        el = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{label}")')
                        el.click()
                        print(f"✅ 已选择目标日期: {label}")
                        self.wait_step(1)
                        return True
                    except Exception as e:
                        print(f"⚠️ 文案存在但点击失败: {label}, {e}")

            # 退化策略：按日(instance)点击
            instance_idx = 0 if (target.year == today.year and target.month == today.month) else 1
            try:
                el = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{target.day}").instance({instance_idx})')
                el.click()
                print(f"✅ 退化策略选择日期: {self.depart_date} (text={target.day}, instance={instance_idx})")
                self.wait_step(1)
                return True
            except Exception as e:
                print(f"❌ 退化策略失败，无法选择日期: {e}")
                return False

        except Exception as e:
            print(f"❌ 日期选择流程异常: {e}")
            return False
   
    def step5_click_search(self):
        """步骤5: 点击查询按钮（带页面刷新）"""
        print("\n🔍 步骤5: 点击查询按钮")
        self.update_task_status("点击查询按钮")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 尝试 {attempt}/{max_attempts}")
            
            try:
                # 点击查询按钮
                search_button = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                      'new UiSelector().text("查询")')
                search_button.click()
                print("✅ 查询按钮已点击")
                
                self.wait_step()
                return True
                
            except NoSuchElementException:
                print(f"⚠️ 第{attempt}次尝试：查询按钮未找到")
                
                if attempt < max_attempts:
                    print("🔄 刷新当前页面...")
                    try:
                        # 刷新页面
                        self.driver.refresh()
                        print("✅ 页面已刷新")
                        self.wait_step(2)  # 等待2秒让页面加载
                    except Exception as e:
                        print(f"⚠️ 页面刷新失败: {e}")
                        # 尝试其他刷新方法
                        try:
                            self.driver.back()
                            self.wait_step(1)
                            self.driver.forward()
                            print("✅ 使用前进后退刷新页面")
                        except Exception as e2:
                            print(f"⚠️ 前进后退刷新也失败: {e2}")
                else:
                    print("❌ 3次尝试后仍未找到查询按钮")
                    # 截图并结束
                    self.take_screenshot_and_exit("查询按钮未找到")
                    return False
                    
            except Exception as e:
                print(f"❌ 第{attempt}次尝试失败: {e}")
                if attempt >= max_attempts:
                    self.take_screenshot_and_exit(f"点击查询失败: {e}")
                    return False
                self.wait_step(2)
        
        return False
    
    def step6_check_flight_list(self):
        """步骤6: 检查航班列表页面并设置价格排序"""
        print("\n📋 步骤6: 检查航班列表页面")
        self.update_task_status("检查航班列表页面")
        
        try:
            # 检查航班列表页面
            flight_list = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                'new UiSelector().text("航班列表")')
            print("✅ 航班列表页面已找到")
            
            # 点击价格排序按钮
            print("🔄 设置价格排序（从低到高）...")
            try:
                price_button = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                     'new UiSelector().text("价格")')
                price_button.click()
                print("✅ 价格排序按钮已点击")
                time.sleep(2)
                
                # 检查是否切换为"价格 低-高"
                try:
                    price_sorted = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                         'new UiSelector().text("价格 低-高")')
                    print("✅ 价格排序已设置为从低到高")
                except:
                    print("⚠️ 价格排序状态未确认，继续执行")
                    
            except Exception as e:
                print(f"⚠️ 价格排序设置失败: {e}，继续执行")
            
            self.wait_step()
            return True
            
        except NoSuchElementException:
            print("❌ 航班列表页面未找到")
            return False
        except Exception as e:
            print(f"❌ 检查航班列表失败: {e}")
            return False
    
    def step7_extract_page_source(self):
        """步骤7: 提取页面源码"""
        print("\n📄 步骤7: 提取页面源码")
        self.update_task_status("提取页面源码")
        
        try:
            # 等待页面完全加载
            print("⏳ 等待页面完全加载...")
            time.sleep(5)
            
            # 智能滚动页面以加载更多内容
            print("🔄 智能滚动页面以加载更多航班信息...")
            try:
                previous_content = ""
                no_change_count = 0
                max_scrolls = 10  # 最大滚动次数
                
                for i in range(max_scrolls):
                    print(f"🔄 第{i+1}次滚动...")
                    
                    # 向上滚动
                    self.driver.swipe(500, 1500, 500, 500, 1000)
                    time.sleep(1)
                    
                    # 向下滚动
                    self.driver.swipe(500, 500, 500, 1500, 1000)
                    time.sleep(1)
                    
                    # 获取当前页面内容进行对比
                    current_content = self.driver.page_source
                    
                    # 检查内容是否有变化
                    if current_content == previous_content:
                        no_change_count += 1
                        print(f"⚠️ 第{no_change_count}次检测到内容无变化")
                        
                        # 如果连续两次滚动后内容无变化，终止滚动
                        if no_change_count >= 2:
                            print("✅ 检测到内容无变化，终止滚动")
                            break
                    else:
                        no_change_count = 0
                        print(f"✅ 检测到新内容，继续滚动")
                    
                    previous_content = current_content
                
                # 最后再向上滚动到顶部
                self.driver.swipe(500, 1500, 500, 500, 1000)
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ 滚动失败: {e}")
                pass
            
            # 获取页面源码
            page_source = self.driver.page_source
            print(f"✅ 页面源码已提取，长度: {len(page_source)} 字符")
            
            # 保存页面源码到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"flight_page_source_{timestamp}.xml")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"💾 页面源码已保存到: {filename}")
            
            return page_source
            
        except Exception as e:
            print(f"❌ 提取页面源码失败: {e}")
            return None
    
    def parse_flight_info(self, page_source):
        """解析航班信息"""
        print("\n🔍 解析航班信息...")
        
        try:
            # 首先尝试使用高级方法解析
            print("🔄 使用高级方法解析航班信息...")
            flights = self.extract_flight_info_advanced(page_source)
            
            if flights:
                print(f"✅ 高级方法找到 {len(flights)} 个航班信息")
                return flights
            
            # 如果高级方法失败，尝试使用备用方法（正则表达式）直接解析
            print("🔄 使用正则表达式方法解析航班信息...")
            flights = self.extract_flight_info_alternative(page_source)
            
            if flights:
                print(f"✅ 正则表达式方法找到 {len(flights)} 个航班信息")
                return flights
            
            # 如果正则表达式方法失败，尝试XPath方法
            print("🔄 尝试XPath方法解析航班信息...")
            root = etree.fromstring(page_source.encode('utf-8') if isinstance(page_source, str) else page_source)
            
            # 更广泛的XPath选择器
            xpath_selectors = [
                '//*[contains(@class, "flight")]',
                '//*[contains(@text, "航班")]',
                '//*[contains(@text, "出发")]',
                '//*[contains(@text, "到达")]',
                '//*[contains(@text, "时间")]',
                '//*[contains(@text, "价格")]',
                '//*[contains(@text, "元")]',
                '//*[contains(@text, "￥")]',
                '//*[contains(@text, "¥")]'
            ]
            
            flight_elements = []
            for selector in xpath_selectors:
                elements = root.xpath(selector)
                flight_elements.extend(elements)
                if elements:
                    print(f"✅ XPath选择器 '{selector}' 找到 {len(elements)} 个元素")
            
            # 去重
            flight_elements = list(set(flight_elements))
            print(f"📊 总共找到 {len(flight_elements)} 个候选元素")
            
            for element in flight_elements:
                flight_info = self.extract_flight_data(element)
                if flight_info:
                    flights.append(flight_info)
            
            print(f"✅ 解析完成，找到 {len(flights)} 个航班信息")
            return flights
            
        except Exception as e:
            print(f"❌ 解析航班信息失败: {e}")
            return []
    
    def extract_flight_data(self, element):
        """从元素中提取航班数据"""
        try:
            flight_info = {
                'airline': '',
                'flight_number': '',
                'departure_date': '',
                'departure_time': '',
                'departure_airport': '',
                'arrival_time': '',
                'arrival_airport': '',
                'flight_duration': '',
                'price': ''
            }
            
            # 提取文本内容（兼容 @text 与节点文本）
            text = (element.get('text', '') or (''.join(element.itertext()) if hasattr(element, 'itertext') else '')).strip()
            
            # 使用正则表达式提取航班信息
            # 航班号模式: 如 CA1234, MU5678，支持前置中文航空公司名
            flight_pattern = r'(?:[\u4e00-\u9fa5]{2,6})?\s*([A-Z]{2}\d{3,4})'
            flight_match = re.search(flight_pattern, text)
            if flight_match:
                flight_info['flight_number'] = flight_match.group(1)
            
            # 时间模式: 如 08:30, 14:25
            time_pattern = r'(\d{1,2}:\d{2})'
            times = re.findall(time_pattern, text)
            if len(times) >= 2:
                flight_info['departure_time'] = times[0]
                flight_info['arrival_time'] = times[1]
                
                # 计算飞行时长
                try:
                    dep_hour, dep_min = map(int, times[0].split(':'))
                    arr_hour, arr_min = map(int, times[1].split(':'))
                    
                    dep_minutes = dep_hour * 60 + dep_min
                    arr_minutes = arr_hour * 60 + arr_min
                    
                    # 处理跨天情况
                    if arr_minutes < dep_minutes:
                        arr_minutes += 24 * 60
                    
                    duration_minutes = arr_minutes - dep_minutes
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    
                    flight_info['flight_duration'] = f"{hours}h{minutes}m"
                except:
                    pass
            
            # 价格模式: 支持 ￥/¥/CNY 与 元，整数或小数
            price_pattern = r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元'
            price_match = re.search(price_pattern, text)
            if price_match:
                flight_info['price'] = price_match.group(1) or price_match.group(2)
            
            # 出发日期提取
            date_patterns = [
                r'(\d{1,2}月\d{1,2}日)',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{1,2}/\d{1,2})',
                r'(\d{4}-\d{1,2}-\d{1,2})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    flight_info['departure_date'] = date_match.group(1)
                    break
            
            # 如果没有找到日期，使用环境变量中的日期
            if not flight_info['departure_date']:
                depart_date = os.getenv('SCRAPER_DEPART_DATE', '')
                if depart_date:
                    flight_info['departure_date'] = depart_date

            # 机场信息（需要根据实际页面结构调整）
            airport_pattern_iata = r'([A-Z]{3})'
            airports = re.findall(airport_pattern_iata, text)
            if len(airports) >= 2:
                flight_info['departure_airport'] = airports[0]
                flight_info['arrival_airport'] = airports[1]
            else:
                # 简单中文提取（例如 “上海 虹桥 出发” / “北京 首都 到达”）
                dep_match = re.search(r'(出发|始发)[\s\S]{0,6}([\u4e00-\u9fa5]{2,8})', text)
                arr_match = re.search(r'(到达|抵达)[\s\S]{0,6}([\u4e00-\u9fa5]{2,8})', text)
                if dep_match:
                    flight_info['departure_airport'] = dep_match.group(2)
                if arr_match:
                    flight_info['arrival_airport'] = arr_match.group(2)

            # 航空公司中文别名到代码映射
            airline_alias = {
                '国航': 'CA', '中国国际航空': 'CA',
                '东航': 'MU', '中国东方航空': 'MU',
                '南航': 'CZ', '中国南方航空': 'CZ',
                '海航': 'HU', '海南航空': 'HU',
                '川航': '3U', '四川航空': '3U',
                '春秋': '9C', '春秋航空': '9C',
                '首都航空': 'JD',
                '吉祥': 'HO', '吉祥航空': 'HO',
            }
            if not flight_info['flight_number']:
                # 尝试仅凭中文别名推断
                for name, code in airline_alias.items():
                    if name in text:
                        flight_info['airline'] = name
                        break
            else:
                # 根据航司代码反推中文名
                code = flight_info['flight_number'][:2]
                for name, c in airline_alias.items():
                    if c == code:
                        flight_info['airline'] = name
                        break
            
            return flight_info if any(flight_info.values()) else None
            
        except Exception as e:
            print(f"⚠️ 提取航班数据失败: {e}")
            return None
    
    def extract_flight_info_alternative(self, page_source):
        """备用方法提取航班信息"""
        print("🔄 使用备用方法提取航班信息...")
        
        flights = []
        
        try:
            # 使用正则表达式直接从页面源码中提取
            # 航班号（带中文别名也可）
            flight_numbers = re.findall(r'(?:[\u4e00-\u9fa5]{2,6})?\s*([A-Z]{2}\d{3,4})', page_source)
            print(f"📊 找到 {len(flight_numbers)} 个航班号")
            
            # 时间
            times = re.findall(r'(\d{1,2}:\d{2})', page_source)
            print(f"📊 找到 {len(times)} 个时间")
            
            # 价格（￥/元/CNY，整数或小数）
            prices = []
            for m in re.finditer(r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元', page_source):
                prices.append(m.group(1) or m.group(2))
            print(f"📊 找到 {len(prices)} 个价格")
            
            # 机场代码
            airports = re.findall(r'([A-Z]{3})', page_source)
            print(f"📊 找到 {len(airports)} 个机场代码")
            
            # 出发日期
            dates = re.findall(r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})', page_source)
            print(f"📊 找到 {len(dates)} 个日期")
            
            # 组合航班信息 - 处理所有找到的时间对，即使没有航班号
            time_pairs = []
            for i in range(0, len(times), 2):
                if i + 1 < len(times):
                    time_pairs.append((times[i], times[i+1]))
            
            max_flights = min(len(time_pairs), 20)  # 最多处理20个航班
            print(f"🔄 找到 {len(time_pairs)} 个时间对，处理前 {max_flights} 个航班...")
            
            for i, (dep_time, arr_time) in enumerate(time_pairs[:max_flights]):
                # 尝试获取对应的航班号，如果没有则跳过不规范的航班
                if i < len(flight_numbers):
                    flight_num = flight_numbers[i]
                else:
                    # 跳过没有航班号的不规范航班（通常是第5个及以后的航班）
                    print(f"⚠️ 跳过第{i+1}个航班：无标准航班号，时间 {dep_time} -> {arr_time}")
                    continue
                
                # 验证航班号格式
                if not re.match(r'^[A-Z]{2}\d{3,4}$', flight_num):
                    print(f"⚠️ 跳过不规范航班号：{flight_num}")
                    continue
                
                # 创建一个简单的上下文用于解析
                simple_context = f"{flight_num} {dep_time} {arr_time} {prices[i] if i < len(prices) else ''}"
                
                flight_info = {
                    'airline': self.get_airline_from_code(flight_num),
                    'flight_number': flight_num,
                    'is_shared_flight': self.detect_shared_flight(flight_num),
                    'aircraft_type': self.extract_aircraft_type(simple_context),
                    'departure_date': dates[0] if dates else '',  # 使用第一个找到的日期
                    'departure_time': dep_time,
                    'departure_airport': airports[i*2] if i*2 < len(airports) else '',
                    'departure_city': self.get_city_from_airport(airports[i*2] if i*2 < len(airports) else ''),
                    'arrival_time': arr_time,
                    'arrival_airport': airports[i*2+1] if i*2+1 < len(airports) else '',
                    'arrival_city': self.get_city_from_airport(airports[i*2+1] if i*2+1 < len(airports) else ''),
                    'flight_duration': '',
                    'has_stopover': self.detect_stopover(simple_context),
                    'stopover_city': self.extract_stopover_city(simple_context),
                    'stopover_airport': self.extract_stopover_airport(simple_context),
                    'price': prices[i] if i < len(prices) else '',
                    'currency': 'CNY',
                    'cabin_class': self.extract_cabin_class(simple_context),
                    'discount_rate': self.extract_discount_rate(simple_context),
                    'original_price': self.extract_original_price(simple_context),
                    'source': '12306',
                    'status': 'active'
                }
                
                # 计算飞行时长
                if flight_info['departure_time'] and flight_info['arrival_time']:
                    try:
                        dep_hour, dep_min = map(int, flight_info['departure_time'].split(':'))
                        arr_hour, arr_min = map(int, flight_info['arrival_time'].split(':'))
                        
                        dep_minutes = dep_hour * 60 + dep_min
                        arr_minutes = arr_hour * 60 + arr_min
                        
                        # 处理跨天情况
                        if arr_minutes < dep_minutes:
                            arr_minutes += 24 * 60
                        
                        duration_minutes = arr_minutes - dep_minutes
                        hours = duration_minutes // 60
                        minutes = duration_minutes % 60
                        
                        flight_info['flight_duration'] = f"{hours}h{minutes}m"
                    except:
                        pass
                
                # 设置航空公司
                flight_info['airline'] = self.get_airline_from_code(flight_num)
                
                flights.append(flight_info)
                print(f"✅ 航班 {i+1}: {flight_info['flight_number']} - {flight_info['departure_time']} -> {flight_info['arrival_time']} - {flight_info['price']}元")
            
        except Exception as e:
            print(f"❌ 备用方法提取失败: {e}")
        
        return flights
    
    def get_airline_from_code(self, flight_number):
        """根据航班号获取航空公司"""
        airline_codes = {
            # 主要航空公司
            'CA': '中国国际航空',
            'MU': '中国东方航空', 
            'CZ': '中国南方航空',
            'HU': '海南航空',
            '3U': '四川航空',
            '9C': '春秋航空',
            'JD': '首都航空',
            'HO': '吉祥航空',
            'ZH': '深圳航空',
            'G5': '华夏航空',
            'KN': '联合航空',
            '8L': '祥鹏航空',
            'TV': '西藏航空',
            'SC': '山东航空',
            'PN': '西部航空',
            'GJ': '长龙航空',
            'Y8': '扬子江航空',
            'QW': '青岛航空',
            'UQ': '乌鲁木齐航空',
            'GT': '桂林航空',
            'DZ': '东海航空',
            'A6': '长龙航空',
            'EU': '成都航空',
            'RY': '瑞丽航空',
            'DR': '瑞丽航空',
            'GX': '北部湾航空',
            'FU': '福州航空',
            'KY': '昆明航空',
            'LT': '龙江航空',
            'OQ': '重庆航空',
            'QW': '青岛航空',
            'UQ': '乌鲁木齐航空',
            'GT': '桂林航空',
            'DZ': '东海航空',
            'A6': '长龙航空',
            'EU': '成都航空',
            'RY': '瑞丽航空',
            'DR': '瑞丽航空',
            'GX': '北部湾航空',
            'FU': '福州航空',
            'KY': '昆明航空',
            'LT': '龙江航空',
            'OQ': '重庆航空'
        }
        
        if len(flight_number) >= 2:
            code = flight_number[:2]
            return airline_codes.get(code, f'{code}航空')
        return '未知航空公司'
    
    def detect_shared_flight(self, flight_number):
        """检测是否为共享航班"""
        # 共享航班通常有特定的标识，这里简化处理
        if '共享' in flight_number or 'SHARE' in flight_number.upper():
            return '是'
        return '否'
    
    def extract_aircraft_type(self, context):
        """提取飞机型号"""
        aircraft_patterns = [
            r'([A-Z]\d{3})',  # 如 A320, B737
            r'(空客\w+)',     # 空客系列
            r'(波音\w+)',     # 波音系列
            r'(A\d{3})',      # 空客型号
            r'(B\d{3})',      # 波音型号
        ]
        
        for pattern in aircraft_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return ''
    
    def get_city_from_airport(self, airport_code):
        """根据机场代码获取城市名称"""
        airport_city_map = {
            'PEK': '北京', 'SHA': '上海', 'PVG': '上海', 'CAN': '广州', 'SZX': '深圳',
            'CTU': '成都', 'XIY': '西安', 'KMG': '昆明', 'HGH': '杭州', 'NKG': '南京',
            'TSN': '天津', 'DLC': '大连', 'SJW': '石家庄', 'TYN': '太原', 'HET': '呼和浩特',
            'HRB': '哈尔滨', 'CGQ': '长春', 'SHE': '沈阳', 'URC': '乌鲁木齐',
            'UTF': '乌鲁木齐', 'QAA': '北京', 'AAB': '北京', 'JRU': '上海',
            'CGJ': '上海', 'BKU': '广州', 'DIR': '深圳', 'AAA': '成都',
            'AAS': '西安', 'UVO': '昆明'
        }
        return airport_city_map.get(airport_code, '')
    
    def detect_stopover(self, context):
        """检测是否经停"""
        stopover_keywords = ['经停', '中转', 'STOP', 'STOPOVER']
        for keyword in stopover_keywords:
            if keyword in context:
                return '是'
        return '否'
    
    def extract_stopover_city(self, context):
        """提取经停城市"""
        # 查找经停相关的城市信息
        stopover_patterns = [
            r'经停[：:]\s*([\u4e00-\u9fa5]+)',
            r'中转[：:]\s*([\u4e00-\u9fa5]+)',
            r'STOP[：:]\s*([\u4e00-\u9fa5]+)',
        ]
        
        for pattern in stopover_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return ''
    
    def extract_stopover_airport(self, context):
        """提取经停机场"""
        # 查找经停机场代码
        airport_pattern = r'经停.*?([A-Z]{3})'
        match = re.search(airport_pattern, context)
        if match:
            return match.group(1)
        return ''
    
    def extract_cabin_class(self, context):
        """提取舱位等级"""
        cabin_patterns = [
            r'(经济舱|商务舱|头等舱|经济|商务|头等)',
            r'(Y|C|F|经济|商务|头等)',
        ]
        
        for pattern in cabin_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return '经济舱'
    
    def extract_discount_rate(self, context):
        """提取折扣率"""
        discount_patterns = [
            r'(\d+折)',
            r'(\d+%)',
            r'折扣[：:]\s*(\d+[折%])',
        ]
        
        for pattern in discount_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return ''
    
    def extract_original_price(self, context):
        """提取原价"""
        original_price_patterns = [
            r'原价[：:]\s*(\d+(?:\.\d+)?)',
            r'原价\s*(\d+(?:\.\d+)?)',
            r'原\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in original_price_patterns:
            match = re.search(pattern, context)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def save_flight_data(self, flights):
        """保存航班数据到数据库和本地文件"""
        if not flights:
            print("❌ 没有航班数据可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"flight_data_{timestamp}.txt")
        
        # 1. 保存到本地文件
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("12306航班信息抓取结果\n")
                f.write("=" * 50 + "\n")
                f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"航班数量: {len(flights)}\n\n")
                
                for i, flight in enumerate(flights, 1):
                    f.write(f"航班 {i}:\n")
                    f.write(f"  航空公司: {flight.get('airline', 'N/A')}\n")
                    f.write(f"  航班号: {flight.get('flight_number', 'N/A')}\n")
                    f.write(f"  是否共享航班: {flight.get('is_shared_flight', 'N/A')}\n")
                    f.write(f"  飞机型号: {flight.get('aircraft_type', 'N/A')}\n")
                    f.write(f"  出发日期: {flight.get('departure_date', 'N/A')}\n")
                    f.write(f"  出发城市: {flight.get('departure_city', 'N/A')}\n")
                    f.write(f"  起飞机场: {flight.get('departure_airport', 'N/A')}\n")
                    f.write(f"  起飞时间: {flight.get('departure_time', 'N/A')}\n")
                    f.write(f"  到达城市: {flight.get('arrival_city', 'N/A')}\n")
                    f.write(f"  落地机场: {flight.get('arrival_airport', 'N/A')}\n")
                    f.write(f"  落地时间: {flight.get('arrival_time', 'N/A')}\n")
                    f.write(f"  飞行时长: {flight.get('flight_duration', 'N/A')}\n")
                    f.write(f"  是否经停: {flight.get('has_stopover', 'N/A')}\n")
                    f.write(f"  经停城市: {flight.get('stopover_city', 'N/A')}\n")
                    f.write(f"  经停机场: {flight.get('stopover_airport', 'N/A')}\n")
                    f.write(f"  最低价格: {flight.get('price', 'N/A')}\n")
                    f.write(f"  舱位等级: {flight.get('cabin_class', 'N/A')}\n")
                    f.write(f"  折扣率: {flight.get('discount_rate', 'N/A')}\n")
                    f.write(f"  原价: {flight.get('original_price', 'N/A')}\n")
                    f.write("-" * 30 + "\n")
            
            print(f"💾 航班数据已保存到: {filename}")
            
        except Exception as e:
            print(f"❌ 保存本地文件失败: {e}")
        
        # 2. 保存到数据库
        try:
            # 获取后端API地址
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            api_url = f"{api_base}/api/flights/batch-save"
            
            # 准备数据
            payload = {
                "flights": flights,
                "source": "12306"
            }
            
            print(f"📤 正在保存 {len(flights)} 条航班数据到数据库...")
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 数据库保存成功: {result.get('message', 'OK')}")
            else:
                print(f"❌ 数据库保存失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
        except Exception as e:
            print(f"❌ 保存到数据库失败: {e}")
    
    def extract_flight_info_advanced(self, page_source):
        """高级方法提取航班信息 - 使用更智能的解析逻辑"""
        print("🔄 使用高级方法提取航班信息...")
        
        flights = []
        
        try:
            # 首先尝试从整个页面源码中提取所有航班号
            all_flight_numbers = re.findall(r'([A-Z]{2}\d{3,4})', page_source)
            print(f"📊 页面中找到 {len(all_flight_numbers)} 个航班号: {all_flight_numbers}")
            
            if not all_flight_numbers:
                print("❌ 高级方法：未找到任何航班号")
                return flights
            
            # 为每个航班号尝试构建航班信息
            for flight_number in all_flight_numbers:
                print(f"🔄 处理航班号: {flight_number}")
                
                # 在页面中查找包含这个航班号的上下文
                flight_context = self.find_flight_context(page_source, flight_number)
                
                if flight_context:
                    flight_info = self.parse_flight_context(flight_context, flight_number)
                    if flight_info:
                        flights.append(flight_info)
                        print(f"✅ 高级方法找到航班: {flight_info['flight_number']} - {flight_info['departure_time']} -> {flight_info['arrival_time']} - {flight_info['price']}元")
                else:
                    print(f"⚠️ 未找到航班 {flight_number} 的上下文信息")
            
        except Exception as e:
            print(f"❌ 高级方法提取失败: {e}")
        
        return flights
    
    def find_flight_context(self, page_source, flight_number):
        """查找航班号的上下文信息"""
        try:
            # 在页面中查找包含航班号的段落或区域
            lines = page_source.split('\n')
            
            for i, line in enumerate(lines):
                if flight_number in line:
                    # 找到包含航班号的行，收集前后几行作为上下文
                    context_lines = []
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    
                    for j in range(start, end):
                        if j < len(lines):
                            context_lines.append(lines[j].strip())
                    
                    context = '\n'.join(context_lines)
                    print(f"📄 航班 {flight_number} 的上下文:\n{context[:200]}...")
                    return context
            
            return None
        except Exception as e:
            print(f"❌ 查找航班上下文失败: {e}")
            return None
    
    def parse_flight_context(self, context, flight_number):
        """解析航班上下文信息"""
        try:
            # 从上下文中提取时间
            times = re.findall(r'(\d{1,2}:\d{2})', context)
            if len(times) < 2:
                print(f"⚠️ 航班 {flight_number} 上下文中的时间不足: {times}")
                return None
            
            # 从上下文中提取价格
            price_match = re.search(r'(?:[¥￥]|CNY)\s*([0-9]+(?:\.[0-9]{1,2})?)|([0-9]+(?:\.[0-9]{1,2})?)\s*元', context)
            price = price_match.group(1) or price_match.group(2) if price_match else ''
            
            if not price:
                print(f"⚠️ 航班 {flight_number} 上下文中未找到价格")
                return None
            
            # 从上下文中提取机场代码
            airports = re.findall(r'([A-Z]{3})', context)
            if len(airports) < 2:
                print(f"⚠️ 航班 {flight_number} 上下文中的机场代码不足: {airports}")
                return None
            
            # 从上下文中提取日期
            date_match = re.search(r'(\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{4}-\d{1,2}-\d{1,2})', context)
            departure_date = date_match.group(1) if date_match else ''
            
            flight_info = {
                'airline': self.get_airline_from_code(flight_number),
                'flight_number': flight_number,
                'departure_date': departure_date,
                'departure_time': times[0],
                'departure_airport': airports[0],
                'arrival_time': times[1],
                'arrival_airport': airports[1],
                'flight_duration': '',
                'price': price,
                'currency': 'CNY',
                'source': '12306',
                'status': 'active'
            }
            
            # 计算飞行时长
            if flight_info['departure_time'] and flight_info['arrival_time']:
                try:
                    dep_hour, dep_min = map(int, flight_info['departure_time'].split(':'))
                    arr_hour, arr_min = map(int, flight_info['arrival_time'].split(':'))
                    
                    dep_minutes = dep_hour * 60 + dep_min
                    arr_minutes = arr_hour * 60 + arr_min
                    
                    # 处理跨天情况
                    if arr_minutes < dep_minutes:
                        arr_minutes += 24 * 60
                    
                    duration_minutes = arr_minutes - dep_minutes
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    
                    flight_info['flight_duration'] = f"{hours}h{minutes}m"
                except:
                    pass
            
            return flight_info
            
        except Exception as e:
            print(f"❌ 解析航班上下文失败: {e}")
            return None
    
    def run_scraping(self, task_id=None):
        """运行完整的抓取流程"""
        print("🚀 开始12306航班信息抓取")
        print("=" * 50)
        
        # 设置任务ID
        if task_id:
            self.set_task_id(task_id)
        
        try:
            # 初始化驱动
            if not self.setup_driver():
                return False
            
            # 执行抓取步骤
            steps = [
                self.step1_launch_12306,
                self.step2_check_homepage,
                self.step3_click_air_rail_transfer,
                self.step4_check_air_rail_page,
                self.step4a_select_from_city,
                self.step4b_select_to_city,
                #self.step4c_select_date,
                self.step5_click_search,
                self.step6_check_flight_list
            ]
            
            for step in steps:
                if not step():
                    print("❌ 抓取流程中断")
                    return False
            
            # 提取页面源码
            page_source = self.step7_extract_page_source()
            if not page_source:
                print("❌ 页面源码提取失败")
                return False
            
            # 解析航班信息
            flights = self.parse_flight_info(page_source)
            
            # 保存数据
            self.save_flight_data(flights)
            
            print("\n🎉 航班信息抓取完成！")
            return True
            
        except Exception as e:
            print(f"❌ 抓取过程出错: {e}")
            return False
        
        finally:
            # 无论成功还是异常，尽力在结束前再留一张最终截图
            try:
                if self.driver:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_shot = os.path.join(self.output_dir, f"flight_scraper_final_{timestamp}.png")
                    self.driver.save_screenshot(final_shot)
                    print(f"📸 最终截图已保存: {final_shot}")
            except Exception as e:
                print(f"⚠️ 最终截图失败: {e}")

            if self.driver:
                self.driver.quit()
                print("🔚 驱动已关闭")

def main():
    """主函数"""
    scraper = FlightScraper12306()
    
    # 从环境变量获取任务ID
    task_id = os.getenv("TASK_ID")
    if task_id:
        try:
            task_id = int(task_id)
        except ValueError:
            task_id = None
    
    success = scraper.run_scraping(task_id)
    
    if success:
        print("\n✅ 抓取任务完成！")
        sys.exit(0)
    else:
        print("\n❌ 抓取任务失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()


