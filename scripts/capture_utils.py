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

def extract_flight_elements_from_xml(page_source, driver=None):
    """
    从页面源码中提取航班相关元素和文本
    提取所有可见的元素（displayed="true"），不限制bounds以读取全部可见区域内容
    如果是WebView页面，也会尝试通过JavaScript获取内容
    
    Args:
        page_source: 页面源码XML字符串
        driver: WebDriver实例（如果为None，读取所有displayed="true"的元素，不限制bounds）
    
    Returns:
        tuple: (unique_flights_set, all_elements_text_set, element_count)
    """
    unique_flights = set()
    all_elements_text = set()
    
    # 如果是WebView页面，尝试通过JavaScript获取内容
    webview_text = None
    if driver:
        try:
            contexts = driver.contexts
            for context in contexts:
                if 'WEBVIEW' in context.upper():
                    try:
                        driver.switch_to.context(context)
                        # 执行JavaScript获取所有文本
                        script = """
                        var texts = [];
                        var walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        var node;
                        while (node = walker.nextNode()) {
                            var text = node.textContent.trim();
                            if (text && text.length > 0) {
                                texts.push(text);
                            }
                        }
                        return texts.join('\\n');
                        """
                        webview_text = driver.execute_script(script)
                        driver.switch_to.context('NATIVE_APP')
                        if webview_text:
                            print(f"✅ 从WebView获取到 {len(webview_text)} 字符的内容")
                            # 从WebView文本中提取航班号
                            webview_flights = re.findall(
                                r'[A-Z]{2,4}\d{3,5}', webview_text)
                            for flight in webview_flights:
                                if len(flight) >= 5 and re.match(
                                        r'^[A-Z]{2,4}\d{3,5}$', flight):
                                    unique_flights.add(flight)
                            # 添加WebView文本到元素集合
                            for line in webview_text.split('\n'):
                                if line.strip():
                                    all_elements_text.add(line.strip())
                        break
                    except Exception as e:

                        try:
                            driver.switch_to.context('NATIVE_APP')
                        except BaseException:

                            pass
                        print(f"⚠️ WebView JavaScript提取失败: {e}")
        except Exception as e:
            print(f"⚠️ 检查WebView上下文失败: {e}")
    
    try:
        # 使用 lxml 解析 XML 源代码，启用错误恢复
        root = etree.fromstring(
            page_source.encode('utf-8'),
            etree.XMLParser(
                recover=True,
                encoding='utf-8'))
        
        # 提取所有文本内容，只提取可见的（displayed="true"）
        # Android: android.widget.TextView
        xpath_query = './/android.widget.TextView[@displayed="true"]'
        current_elements = root.xpath(xpath_query)
        
        visible_count = 0
        for element in current_elements:
            # 检查元素是否可见
            displayed = element.get('displayed', 'false').lower()
            if displayed != 'true':
                continue
            
            # 如果driver为None，不限制bounds，读取所有displayed="true"的元素
            # 这样可以读取滚动后加载的所有可见内容
            if driver is None:
                # 读取所有可见元素，不限制bounds
                visible_count += 1
            else:
                # 如果提供了driver，可以可选地检查bounds（但通常不需要，因为要读取全部内容）
                visible_count += 1
            
            # 获取 Android 的 'text' 属性
            element_text = element.get(
                'text') or element.get('content-desc') or ''
            if element_text and element_text.strip():
                all_elements_text.add(element_text.strip())
                
                # 提取航班号（格式：2-3个大写字母 + 3-4个数字）
                # 修改正则表达式，支持中文前缀（如"深航ZH9515"），不使用单词边界
                # 匹配模式：2-3个大写字母后跟3-4个数字，前面可能有中文字符
                # 使用更宽松的匹配，支持2-4个字母和3-5个数字的组合
                flight_matches = re.findall(r'[A-Z]{2,4}\d{3,5}', element_text)
                # 进一步验证：确保匹配的是有效的航班号格式
                # 标准格式：2-3个字母 + 3-4个数字，但也接受2-4个字母 + 3-5个数字的变体
                valid_flights = []
                for f in flight_matches:
                    # 验证格式：至少2个字母，至少3个数字，总长度至少5
                    if len(f) >= 5 and re.match(r'^[A-Z]{2,4}\d{3,5}$', f):
                        # 标准化：如果是4个字母或5个数字，可能是误匹配，但先接受
                        valid_flights.append(f)
                unique_flights.update(valid_flights)
        
        return unique_flights, all_elements_text, visible_count
        
    except Exception as e:

        print(f"⚠️ XML解析失败，使用正则表达式回退: {e}")
        # 回退方案：直接使用正则表达式从字符串中提取
        # 修改正则表达式，支持中文前缀，不使用单词边界
        all_matches = re.findall(r'[A-Z]{2,3}\d{3,4}', page_source)
        # 验证匹配结果的格式
        unique_flights = set([f for f in all_matches if len(
            f) >= 5 and re.match(r'^[A-Z]{2,3}\d{3,4}$', f)])
        return unique_flights, set(), 0



