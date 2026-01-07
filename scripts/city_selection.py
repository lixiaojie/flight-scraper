# -*- coding: utf-8 -*-
# 此文件由 page_capture.py 分拆而来
# 包含所有城市选择相关的函数

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
from io import StringIO, BytesIO
from utils import tprint, wait_step, parse_bounds

# OCR相关导入
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR库未安装，将使用备用方法判断城市选择页面")

def get_city_pinyin_initials(city_name):
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
        # 更多城市
        '大同': 'DT', '包头': 'BT', '鄂尔多斯': 'EEDS', '赤峰': 'CF',
        '通辽': 'TL', '呼伦贝尔': 'HLBE', '巴彦淖尔': 'BYNE',
        '秦皇岛': 'QHD', '唐山': 'TS', '保定': 'BD', '廊坊': 'LF',
        '邯郸': 'HD', '张家口': 'ZJK', '承德': 'CD', '沧州': 'CZ',
        '衡水': 'HS', '邢台': 'XT', '吉林': 'JL', '延边': 'YB',
        '白山': 'BS', '白城': 'BC', '辽源': 'LY', '通化': 'TH',
        '松原': 'SY', '四平': 'SP', '齐齐哈尔': 'QQHE', '牡丹江': 'MDJ',
        '佳木斯': 'JMS', '大庆': 'DQ', '鸡西': 'JX', '绥化': 'SH',
        '鹤岗': 'HG', '双鸭山': 'SYS', '伊春': 'YC', '七台河': 'QTH',
        '黑河': 'HH', '大兴安岭': 'DXAL', '烟台': 'YT', '威海': 'WH',
        '潍坊': 'WF', '淄博': 'ZB', '临沂': 'LY', '东营': 'DY',
        '泰安': 'TA', '济宁': 'JN', '聊城': 'LC', '德州': 'DZ',
        '滨州': 'BZ', '枣庄': 'ZZ', '日照': 'RZ', '菏泽': 'HZ',
        '莱芜': 'LW', '洛阳': 'LY', '开封': 'KF', '安阳': 'AY',
        '新乡': 'XX', '焦作': 'JZ', '许昌': 'XC', '平顶山': 'PDS',
        '漯河': 'LH', '南阳': 'NY', '信阳': 'XY', '周口': 'ZK',
        '驻马店': 'ZMD', '商丘': 'SQ', '三门峡': 'SMX', '濮阳': 'PY',
        '鹤壁': 'HB', '济源': 'JY', '襄阳': 'XY', '宜昌': 'YC',
        '荆州': 'JZ', '荆门': 'JM', '十堰': 'SY', '黄冈': 'HG',
        '孝感': 'XG', '咸宁': 'XN', '随州': 'SZ', '恩施': 'ES',
        '鄂州': 'EZ', '黄石': 'HS', '岳阳': 'YY', '衡阳': 'HY',
        '株洲': 'ZZ', '常德': 'CD', '郴州': 'CZ', '湘潭': 'XT',
        '邵阳': 'SY', '娄底': 'LD', '永州': 'YZ', '益阳': 'YY',
        '怀化': 'HH', '张家界': 'ZJJ', '湘西': 'XX', '惠州': 'HZ',
        '江门': 'JM', '湛江': 'ZJ', '汕头': 'ST', '肇庆': 'ZQ',
        '茂名': 'MM', '揭阳': 'JY', '清远': 'QY', '梅州': 'MZ',
        '韶关': 'SG', '汕尾': 'SW', '河源': 'HY', '阳江': 'YJ',
        '潮州': 'CZ', '云浮': 'YF', '南宁': 'NN', '桂林': 'GL',
        '柳州': 'LZ', '北海': 'BH', '玉林': 'YL', '百色': 'BS',
        '梧州': 'WZ', '钦州': 'QZ', '贵港': 'GG', '河池': 'HC',
        '崇左': 'CZ', '来宾': 'LB', '贺州': 'HZ', '防城港': 'FCG',
        '绵阳': 'MY', '宜宾': 'YB', '德阳': 'DY', '泸州': 'LZ',
        '南充': 'NC', '乐山': 'LS', '自贡': 'ZG', '遂宁': 'SN',
        '内江': 'NJ', '达州': 'DZ', '眉山': 'MS', '广安': 'GA',
        '资阳': 'ZY', '攀枝花': 'PZH', '广元': 'GY', '巴中': 'BZ',
        '雅安': 'YA', '遵义': 'ZY', '六盘水': 'LPS', '安顺': 'AS',
        '毕节': 'BJ', '铜仁': 'TR', '黔东南': 'QDN', '黔南': 'QN',
        '黔西南': 'QXN', '曲靖': 'QJ', '玉溪': 'YX', '大理': 'DL',
        '红河': 'HH', '楚雄': 'CX', '文山': 'WS', '普洱': 'PE',
        '昭通': 'ZT', '保山': 'BS', '丽江': 'LJ', '临沧': 'LC',
        '德宏': 'DH', '西双版纳': 'XSBN', '怒江': 'NJ', '迪庆': 'DQ',
        '咸阳': 'XY', '宝鸡': 'BJ', '渭南': 'WN', '延安': 'YA',
        '汉中': 'HZ', '榆林': 'YL', '安康': 'AK', '商洛': 'SL',
        '铜川': 'TC', '天水': 'TS', '白银': 'BY', '平凉': 'PL',
        '庆阳': 'QY', '定西': 'DX', '陇南': 'LN', '武威': 'WW',
        '张掖': 'ZY', '酒泉': 'JQ', '嘉峪关': 'JYG', '金昌': 'JC',
        '临夏': 'LX', '甘南': 'GN', '海东': 'HD', '海北': 'HB',
        '海南州': 'HNZ', '黄南': 'HN', '果洛': 'GL', '玉树': 'YS',
        '海西': 'HX', '石嘴山': 'SZS', '吴忠': 'WZ', '固原': 'GY',
        '中卫': 'ZW', '克拉玛依': 'KLMY', '吐鲁番': 'TLF', '哈密': 'HM',
        '昌吉': 'CJ', '博尔塔拉': 'BETL', '巴音郭楞': 'BYGL',
        '阿克苏': 'AKS', '喀什': 'KS', '和田': 'HT', '伊犁': 'YL',
        '塔城': 'TC', '阿勒泰': 'ALT', '日喀则': 'RKZ', '山南': 'SN',
        '林芝': 'LZ', '昌都': 'CD', '那曲': 'NQ', '阿里': 'AL',
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
        '拉': 'L', '萨': 'S', '口': 'K', '三': 'S', '亚': 'Y', '珠': 'Z',
        '中': 'Z', '山': 'S', '东': 'D', '莞': 'G', '佛': 'F', '无': 'W',
        '锡': 'X', '常': 'C', '通': 'T', '温': 'W', '台': 'T', '嘉': 'J',
        '兴': 'X', '绍': 'S', '金': 'J', '华': 'H', '湖': 'H', '舟': 'Z',
        '丽': 'L', '水': 'S', '衢': 'Q', '波': 'B', '扬': 'Y', '泰': 'T',
        '镇': 'Z', '江': 'J', '盐': 'Y', '城': 'C', '淮': 'H', '宿': 'S',
        '迁': 'Q', '云': 'Y', '港': 'G', '徐': 'X', '蚌': 'B', '埠': 'B',
        '滁': 'C', '六': 'L', '马': 'M', '鞍': 'A', '芜': 'W', '宣': 'X',
        '铜': 'T', '陵': 'L', '池': 'C', '庆': 'Q', '黄': 'H', '阜': 'F',
        '亳': 'B',
    }
    
    # 尝试组合每个汉字的首字母
    if city_name:
        result = ''
        for char in city_name:
            if char in char_pinyin:
                result += char_pinyin[char]
            elif '\u4e00' <= char <= '\u9fff':

                # 对于未知汉字，使用占位符或跳过
                result += char[0] if char else ''
        if result:
            return result
    
    # 最后的兜底方案：返回城市名本身（虽然可能不准确）
    return city_name if city_name else 'BJ'



def find_city_element(driver, city_type='出发', city_name=None):
    """
    查找出发城市或到达城市的元素

    优先使用 UiSelector 缩小范围，然后按顺序识别（第一个=出发，第二个=到达）
    如果失败，回退到 resource-id、content-desc 或文本标签识别
    
    Args:
        driver: WebDriver实例
        city_type: '出发' 或 '到达'
        city_name: 当前显示的城市名称（可选，用于精确定位）
    
    Returns:
        tuple: (WebElement or None, dict or None) - 元素和位置信息
    """
    print(f"🔍 查找{city_type}城市元素...")
    
    # 策略0（最高优先级）：使用 UiSelector 缩小范围
    # 在 new UiSelector().className("android.view.View").instance(13) 内查找城市
    # 前一个城市为出发，后一个城市为到达，中间相隔 instance(14)
    try:
        print("🔄 策略0: 使用 UiSelector 缩小范围查找城市元素...")
        # 尝试在指定的 View 容器内查找城市元素
        container_selector = 'new UiSelector().className("android.view.View").instance(13)'
        
        # 查找容器内的所有 TextView 元素（城市通常是 TextView）
        city_text_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'{container_selector}.childSelector(new UiSelector().className("android.widget.TextView"))'
        )
        
        # 如果上面的方法失败，尝试另一种方式：先找到容器，再查找子元素
        if not city_text_elements:
            try:
                container = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    container_selector
                )
                # 在容器内查找所有 TextView
                city_text_elements = container.find_elements(
                    AppiumBy.CLASS_NAME,
                    "android.widget.TextView"
                )
            except:
                pass
        
        # 筛选出城市元素（2-4个中文字符）
        city_candidates = []
        for elem in city_text_elements:
            try:
                text = elem.text
                if text and 2 <= len(text) <= 4 and all('\u4e00' <= c <= '\u9fff' for c in text):
                    location = elem.location
                    size = elem.size
                    center_x = location['x'] + size['width'] // 2
                    center_y = location['y'] + size['height'] // 2
                    city_candidates.append({
                        'element': elem,
                        'text': text,
                        'center': (center_x, center_y),
                        'x': center_x
                    })
            except:
                continue
        
        # 按 x 坐标排序（从左到右）
        city_candidates.sort(key=lambda x: x['x'])
        
        if len(city_candidates) >= 2:
            # 第一个城市是出发，第二个是到达
            if city_type == '出发':
                selected = city_candidates[0]
                print(f"✅ 策略0成功: 在 View.instance(13) 内找到出发城市（第一个）: {selected['text']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
            else:  # 到达
                selected = city_candidates[1]
                print(f"✅ 策略0成功: 在 View.instance(13) 内找到到达城市（第二个）: {selected['text']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
        elif len(city_candidates) == 1:
            # 如果只找到一个城市，根据 city_type 判断
            if city_type == '出发':
                selected = city_candidates[0]
                print(f"✅ 策略0部分成功: 在 View.instance(13) 内只找到一个城市，作为出发城市: {selected['text']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
    except Exception as e:
        print(f"⚠️ 策略0失败: {e}")
    
    # 策略0.5：按顺序提取所有城市元素（第一个=出发，第二个=到达）
    try:
        print("🔄 策略0.5: 按顺序提取城市元素（第一个=出发，第二个=到达）...")
        # 查找页面中所有符合条件的城市元素
        all_city_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.TextView")'
        )
        
        city_candidates = []
        for elem in all_city_elements:
            try:
                text = elem.text
                if text and 2 <= len(text) <= 4 and all('\u4e00' <= c <= '\u9fff' for c in text):
                    location = elem.location
                    size = elem.size
                    center_x = location['x'] + size['width'] // 2
                    center_y = location['y'] + size['height'] // 2
                    # 只考虑在城市选择区域的元素（y坐标在合理范围内）
                    if 500 <= center_y <= 800:
                        city_candidates.append({
                            'element': elem,
                            'text': text,
                            'center': (center_x, center_y),
                            'x': center_x
                        })
            except:
                continue
        
        # 按 x 坐标排序（从左到右）
        city_candidates.sort(key=lambda x: x['x'])
        
        if len(city_candidates) >= 2:
            # 第一个城市是出发，第二个是到达
            if city_type == '出发':
                selected = city_candidates[0]
                print(f"✅ 策略0.5成功: 按顺序找到出发城市（第一个）: {selected['text']}, x坐标: {selected['x']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
            else:  # 到达
                selected = city_candidates[1]
                print(f"✅ 策略0.5成功: 按顺序找到到达城市（第二个）: {selected['text']}, x坐标: {selected['x']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
        elif len(city_candidates) == 1:
            # 如果只找到一个城市，根据 city_type 判断
            if city_type == '出发':
                selected = city_candidates[0]
                print(f"✅ 策略0.5部分成功: 只找到一个城市，作为出发城市: {selected['text']}")
                return selected['element'], {'text': selected['text'], 'center': selected['center']}
    except Exception as e:
        print(f"⚠️ 策略0.5失败: {e}")
    
    # 首先尝试从页面源码中查找城市元素及其位置（原有策略）
    try:
        page_source = driver.page_source
        root = etree.fromstring(page_source.encode('utf-8'))
        import re

        # 策略1：优先使用 resource-id 或 content-desc 来识别城市类型
        # 查找包含"出发"或"到达"标签的父元素，然后在其附近查找城市元素
        city_label_keywords = {
            '出发': ['出发', 'from', 'departure', 'depart'],
            '到达': ['到达', 'to', 'arrival', 'arrive', 'destination']
        }

        city_elements = []
        label_keywords = city_label_keywords.get(city_type, [])

        # 查找包含城市类型标签的元素（如"出发"、"到达"）
        for keyword in label_keywords:
            # 查找包含标签文本的元素
            label_xpath = f'.//*[contains(@text, "{keyword}") or contains(@content-desc, "{keyword}") or contains(@resource-id, "{keyword}")]'
            label_elements = root.xpath(label_xpath)

            for label_elem in label_elements:
                label_bounds = label_elem.get('bounds', '')
                if not label_bounds:
                    continue

                try:
                    match = re.search(
                        r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', label_bounds)
                    if match:
                        label_x1, label_y1, label_x2, label_y2 = map(
                            int, match.groups())
                        label_center_x = (label_x1 + label_x2) // 2
                        label_center_y = (label_y1 + label_y2) // 2

                        # 在标签附近查找城市元素（同一行或下方）
                        # 查找所有城市文本元素
                        all_text_elements = root.xpath('.//*[@text]')
                        for city_elem in all_text_elements:
                            city_text = city_elem.get('text', '').strip()
                            city_bounds = city_elem.get('bounds', '')

                            # 城市名通常是2-4个中文字符
                            if city_text and 2 <= len(city_text) <= 4 and all(
                                    '\u4e00' <= c <= '\u9fff' for c in city_text):
                                if city_bounds:
                                    try:
                                        match = re.search(
                                            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', city_bounds)
                                        if match:
                                            city_x1, city_y1, city_x2, city_y2 = map(
                                                int, match.groups())
                                            city_center_x = (
                                                city_x1 + city_x2) // 2
                                            city_center_y = (
                                                city_y1 + city_y2) // 2

                                            # 检查城市元素是否在标签附近（同一行，y坐标相近，x坐标在标签右侧）
                                            if abs(
                                                    city_center_y - label_center_y) < 100 and city_center_x > label_center_x - 50:
                                                city_elements.append({
                                                    'text': city_text,
                                                    'bounds': city_bounds,
                                                    'center': (city_center_x, city_center_y),
                                                    'element': city_elem,
                                                    'label': keyword,
                                                    'label_center': (label_center_x, label_center_y)
                                                })
                                                print(
                                                    f"✅ 通过标签'{keyword}'找到{city_type}城市元素: {city_text}, 位置: {city_bounds}")
                                    except BaseException:

                                        pass

                except BaseException:
                    pass

        # 策略2：如果策略1失败，尝试通过 resource-id 或 content-desc 直接查找
    except Exception as e:

        print(f"⚠️ 从页面源码查找失败: {e}")

        if not city_elements:
            for keyword in label_keywords:
                # 查找 resource-id 或 content-desc 包含关键词的可点击元素
                xpath_query = f'.//*[contains(@resource-id, "{keyword}") or contains(@content-desc, "{keyword}")]'
                elements = root.xpath(xpath_query)

                for elem in elements:
                    bounds = elem.get('bounds', '')
                    resource_id = elem.get('resource-id', '')
                    content_desc = elem.get('content-desc', '')
                    text = elem.get('text', '').strip()

                    if bounds:
                        try:
                            match = re.search(
                                r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                            if match:
                                x1, y1, x2, y2 = map(int, match.groups())
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2

                                # 检查是否在城市选择区域
                                if 400 <= center_y <= 900:
                                    city_elements.append({
                                        'text': text or city_name or '城市',
                                        'bounds': bounds,
                                        'center': (center_x, center_y),
                                        'element': elem,
                                        'resource_id': resource_id,
                                        'content_desc': content_desc
                                    })
                                    print(
                                        f"✅ 通过resource-id/content-desc找到{city_type}城市元素: resource-id={resource_id}, content-desc={content_desc}, text={text}")
                        except BaseException:

                            pass

        # 策略3：如果前两种策略都失败，且提供了城市名，尝试查找该城市名
        if not city_elements and city_name:
            xpath_query = f'.//android.widget.TextView[@text="{city_name}"]'
            elements = root.xpath(xpath_query)
            for elem in elements:
                bounds = elem.get('bounds', '')
                if bounds:
                    try:
                        match = re.search(
                            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            # 检查是否在合理的区域
                            if 400 <= center_y <= 900:
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

            # 如果找到多个同名城市元素，优先使用通过标签找到的
            if len(city_elements) > 1:
                # 优先选择有标签信息的元素
                labeled_elements = [e for e in city_elements if 'label' in e]
                if labeled_elements:
                    city_elements = labeled_elements
                    print(f"🔍 优先选择通过标签找到的元素")
                else:
                    # 如果没有标签信息，根据city_type筛选（作为最后手段）
                    print(
                        f"⚠️ 找到 {len(city_elements)} 个同名城市元素 '{city_name}'，根据位置筛选（最后手段）")
                    if city_type == '出发':
                        city_elements = [
                            min(city_elements, key=lambda x: x['center'][0])]
                        print(
                            f"🔍 筛选后选择出发城市元素: {city_elements[0]['text']}, x={city_elements[0]['center'][0]}")
                    else:
                        city_elements = [
                            max(city_elements, key=lambda x: x['center'][0])]
                        print(
                            f"🔍 筛选后选择到达城市元素: {city_elements[0]['text']}, x={city_elements[0]['center'][0]}")

        # 如果没有找到或未提供城市名，尝试查找所有可能的城市元素
        if not city_elements:
            # 扩大搜索范围：查找所有类型的元素（不仅仅是TextView）
            all_elements = root.xpath('.//*[@text]')
            screen_size = driver.get_window_size()
            screen_height = screen_size.get('height', 2400)
            y_min = 400
            y_max = min(900, screen_height * 0.4)

            for elem in all_elements:
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
                            # 检查是否在城市选择区域（扩大范围）
                            if y_min <= center_y <= y_max and 50 <= center_x <= 1000:
                                city_elements.append({
                                    'text': text,
                                    'bounds': bounds,
                                    'center': (center_x, center_y),
                                    'element': elem
                                })
                                print(
                                    f"🔍 找到候选城市元素: {text}, 位置: {bounds}, 中心: ({center_x}, {center_y})")
                    except BaseException:

                        pass

            # 如果还是没有找到，尝试查找可点击的元素
            if not city_elements:
                print(f"⚠️ 未找到城市文本元素，尝试查找可点击的城市选择区域...")
                clickable_elements = root.xpath('.//*[@clickable="true"]')
                for elem in clickable_elements:
                    bounds = elem.get('bounds', '')
                    resource_id = elem.get('resource-id', '')
                    content_desc = elem.get('content-desc', '')
                    text = elem.get('text', '').strip()

                    if bounds:
                        try:
                            match = re.search(
                                r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                            if match:
                                x1, y1, x2, y2 = map(int, match.groups())
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                # 检查是否在城市选择区域
                                if y_min <= center_y <= y_max and 50 <= center_x <= 1000:
                                    # 检查resource-id或content-desc是否包含城市相关关键词
                                    city_keywords = [
                                        'city', '城市', '出发', '到达', 'from', 'to']
                                    if any(
                                        keyword in (
                                            resource_id +
                                            content_desc +
                                            text).lower() for keyword in city_keywords):
                                        print(
                                            f"🔍 找到可点击的城市选择元素: resource-id={resource_id}, content-desc={content_desc}, text={text}, 位置: {bounds}")
                                        # 尝试通过坐标点击
                                        city_elements.append({
                                            'text': text or '城市',
                                            'bounds': bounds,
                                            'center': (center_x, center_y),
                                            'element': elem
                                        })
                        except BaseException:

                            pass
        
        # 优先使用通过标签找到的元素，如果没有则使用其他方法
            # 优先选择通过标签找到的元素
            labeled_elements = [e for e in city_elements if 'label' in e]
            if labeled_elements:
                # 如果有多个标签元素，选择与city_type匹配的
                city_info = labeled_elements[0]
                print(
                    f"✅ 通过标签找到{city_type}城市元素: {city_info['text']}, 位置: {city_info['bounds']}")
            else:
                # 如果没有标签元素，根据city_type选择（作为最后手段）
                if city_type == '出发':
                    # 出发城市在左侧：选择x坐标最小的元素
                    city_info = min(city_elements, key=lambda x: x['center'][0])
                    print(
                        f"✅ 通过位置找到{city_type}城市元素: {city_info['text']}, 位置: {city_info['bounds']}")
                else:  # 到达
                    # 到达城市在右侧：选择x坐标最大的元素
                    city_info = max(city_elements, key=lambda x: x['center'][0])
                    print(
                        f"⚠️ 使用位置筛选（最后手段）找到{city_type}城市元素: {city_info['text']}, 位置: {city_info['bounds']}, x坐标: {city_info['center'][0]}")
            
            # 尝试通过文本定位元素
            try:
                element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                                            f'new UiSelector().text("{city_info["text"]}")')
                return element, city_info
            except BaseException:

                # 如果无法通过文本定位，返回位置信息用于坐标点击
                print(f"⚠️ 无法通过文本定位元素，将使用坐标点击: {city_info['center']}")
                return None, city_info
        
    except Exception as e:


        print(f"⚠️ 从页面源码查找失败: {e}")
    
    # 备用方案：尝试通过UiSelector查找
    try:
        elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
                                      'new UiSelector().className("android.widget.TextView")')
        candidate_elements = []
        for element in elements:
            try:
                text = element.text
                if text and 2 <= len(text) <= 4 and all(
                        '\u4e00' <= c <= '\u9fff' for c in text):
                    location = element.location
                    size = element.size
                    center_x = location['x'] + size['width'] // 2
                    center_y = location['y'] + size['height'] // 2
                    if 500 <= center_y <= 800:
                        candidate_elements.append({
                            'element': element,
                            'text': text,
                            'center': (center_x, center_y)
                        })
            except BaseException:
                continue
        
        # 如果提供了当前城市名，优先匹配
        if city_name and candidate_elements:
            matching = [e for e in candidate_elements if e['text'] == city_name]
            if matching:
                candidate_elements = matching
        
        # 根据 city_type 筛选
        if candidate_elements:
            if city_type == '出发':
                # 出发城市在左侧：选择x坐标最小的元素
                selected = min(candidate_elements, key=lambda x: x['center'][0])
            else:  # 到达
                # 到达城市在右侧：选择x坐标最大的元素
                selected = max(candidate_elements, key=lambda x: x['center'][0])
            
            print(f"✅ 通过UiSelector找到{city_type}城市元素: {selected['text']}, x坐标: {selected['center'][0]}")
            return selected['element'], {'text': selected['text'], 'center': selected['center']}
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
    
    city_element, city_info = find_city_element(
        driver, city_type, current_city)
    
    try:
        if city_element:
            try:
                city_element.click()
                print(f"✅ 已点击{city_type}城市元素")
            except Exception as e:

                print(f"⚠️ 点击元素失败: {e}，尝试坐标点击")
                if city_info and 'center' in city_info:
                    center_x, center_y = city_info['center']
                    driver.tap([(center_x, center_y)], 100)
                    print(f"✅ 已通过坐标点击{city_type}城市: ({center_x}, {center_y})")
                else:
                    raise
        elif city_info and 'center' in city_info:

            center_x, center_y = city_info['center']
            driver.tap([(center_x, center_y)], 100)
            print(f"✅ 已通过坐标点击{city_type}城市: ({center_x}, {center_y})")
        else:
            print(f"❌ 未找到{city_type}城市元素或位置信息")
            return False
        
        wait_step(driver, 2)
        
        # 使用OCR判断是否进入城市选择页面
        return check_city_selection_page_by_ocr(driver)
            
    except Exception as e:


        print(f"❌ 点击{city_type}城市失败: {e}")
        return False



def check_city_selection_page_by_ocr(driver):
    """
    使用OCR判断是否进入城市选择页面
    
    Args:
        driver: WebDriver实例
    
    Returns:
        bool: 是否成功进入城市选择页面
    """
    print("🔍 使用OCR判断是否进入城市选择页面...")
    
    if not OCR_AVAILABLE:
        print("⚠️ OCR库未安装，使用备用方法判断")
        # 备用方法：查找搜索框
        search_box = find_city_search_box(driver)
        if search_box:
            print("✅ 已进入城市选择页面（通过搜索框检测）")
            return True
        else:
            print("❌ 未检测到城市选择页面")
            return False
    
    try:
        # 获取截图
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot))
        
        # 使用OCR识别（中英文混合）
        custom_config = r'--oem 3 --psm 6'  # PSM 6: 假设统一的文本块
        text = pytesseract.image_to_string(image, lang='chi_sim+eng', config=custom_config)
        
        # 检查是否包含城市选择页面的关键词
        city_selection_keywords = [
            '搜索', '请输入', '城市', 'Search', '城市选择',
            '出发城市', '到达城市', '选择城市', '热门城市', '最近常用'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        for keyword in city_selection_keywords:
            if keyword in text or keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            print(f"✅ 已进入城市选择页面（OCR识别到关键词: {', '.join(found_keywords[:3])}）")
            return True
        else:
            print("⚠️ OCR未识别到城市选择页面关键词，尝试备用方法...")
            # 备用方法：查找搜索框
            search_box = find_city_search_box(driver)
            if search_box:
                print("✅ 已进入城市选择页面（通过搜索框检测）")
                return True
            else:
                print("❌ 未检测到城市选择页面")
                return False
            
    except Exception as e:
        print(f"⚠️ OCR识别失败: {e}，使用备用方法")
        # 备用方法：查找搜索框
        search_box = find_city_search_box(driver)
        if search_box:
            print("✅ 已进入城市选择页面（通过搜索框检测）")
            return True
        else:
            print("❌ 未检测到城市选择页面")
            return False


def verify_returned_to_main_page(driver):
    """
    验证是否返回到主页面（空铁联运页面）
    
    Args:
        driver: WebDriver实例
    
    Returns:
        bool: 是否在主页面
    """
    try:
        # 检查是否包含主页面特征元素
        main_page_indicators = ['查询', '出发', '到达', '日期', '空铁联运']
        
        page_source = driver.page_source
        found_indicators = []
        for indicator in main_page_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        # 如果找到多个主页面特征，认为已返回主页面
        if len(found_indicators) >= 2:
            return True
        
        # 检查是否还在城市选择页面（包含城市选择页面特征）
        city_selection_indicators = ['最近常用', '热门城市', '开启定位']
        found_city_selection = []
        for indicator in city_selection_indicators:
            if indicator in page_source:
                found_city_selection.append(indicator)
        
        # 如果找到城市选择页面特征，说明还在城市选择页面
        if len(found_city_selection) >= 2:
            return False

        # 默认认为已返回主页面
        return True
        
    except Exception as e:
        print(f"⚠️ 验证主页面失败: {e}")
        return True  # 默认返回True，避免阻塞流程


def find_city_search_box(driver):
    """查找城市选择页面的搜索框"""
    print("🔍 查找搜索框...")
    
    try:
        edit_texts = driver.find_elements(
            AppiumBy.CLASS_NAME, "android.widget.EditText")
        if edit_texts:
            search_box = edit_texts[0]
            print("✅ 找到搜索框（EditText）")
            return search_box
    except Exception as e:

        print(f"⚠️ 查找EditText失败: {e}")
    
    try:
        for text in ['搜索', '请输入', 'Search', '城市']:
            try:
                element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                                           f'new UiSelector().textContains("{text}")')
                if element.tag_name == 'android.widget.EditText' or 'EditText' in str(
                        element):
                    print(f"✅ 找到搜索框（通过文本: {text}）")
                    return element
            except BaseException:

                continue
    except Exception as e:


        print(f"⚠️ 通过文本查找搜索框失败: {e}")
    
    print("❌ 未找到搜索框")
    return None



def _clean_city_name(city_name):
    """
    清理和验证城市名称，确保只包含有效的汉字城市名称
    
    Args:
        city_name: 原始城市名称
    
    Returns:
        str: 清理后的城市名称
    """
    if not city_name:
        return ""
    
    # 转换为字符串（防止非字符串类型）
    city_name = str(city_name).strip()
    
    # 移除常见的后缀（如"市"、"省"等，但保留城市名称本身）
    # 注意：这里不自动移除"市"，因为有些城市名称本身就包含"市"
    
    # 只保留中文字符、英文字母和数字（城市名称可能包含英文）
    # 匹配中文字符、英文字母、数字
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', city_name)
    
    # 如果清理后为空，返回原始值（可能是特殊情况）
    if not cleaned:
        return city_name
    
    return cleaned


def input_city_search(driver, city_name):
    """在搜索框中直接输入城市名称（汉字），并等待搜索结果出现"""
    # 清理和验证城市名称
    cleaned_city_name = _clean_city_name(city_name)
    
    if not cleaned_city_name:
        print(f"❌ 城市名称无效或为空: {city_name}")
        return False
    
    # 验证清理后的城市名称
    if cleaned_city_name != city_name:
        print(f"⚠️ 城市名称已清理: '{city_name}' -> '{cleaned_city_name}'")
    
    print(f"\n⌨️ 步骤: 在搜索框输入城市名称 '{cleaned_city_name}'")
    
    search_box = find_city_search_box(driver)
    if not search_box:
        print("❌ 未找到搜索框")
        return False
    
    try:
        # 步骤1: 点击搜索框，确保获得焦点
        try:
            search_box.click()
            print("✅ 已点击搜索框，获得焦点")
            wait_step(driver, 0.5)  # 等待焦点稳定
        except Exception as e:
            print(f"❌ 点击搜索框失败: {e}")
            return False
        
        # 步骤2: 清空搜索框（多次清空确保干净）
        try:
            search_box.clear()
            wait_step(driver, 0.2)
            # 再次清空，确保没有残留内容
            search_box.clear()
            print("✅ 已清空搜索框")
        except BaseException:
            pass
        
        # 步骤3: 输入清理后的城市名称
        # 使用清理后的城市名称，确保只输入有效的城市名称
        search_box.send_keys(cleaned_city_name)
        print(f"✅ 已输入城市名称: {cleaned_city_name}")
        
        # 验证输入的内容（可选，用于调试）
        try:
            # 获取搜索框的文本内容，验证是否正确输入
            input_text = search_box.text
            if input_text and input_text != cleaned_city_name:
                print(f"⚠️ 输入验证: 搜索框内容为 '{input_text}'，预期为 '{cleaned_city_name}'")
        except Exception:
            pass  # 忽略验证错误，继续执行
        
        # 等待输入完成，让应用自动触发搜索
        wait_step(driver, 1)  # 等待应用自动触发搜索
        
        # 等待搜索结果出现（最多等待5秒）
        wait_step(driver, 1)  # 先等待1秒让搜索触发
        
        # 验证搜索结果是否出现
        max_wait = 5
        for i in range(max_wait):
            try:
                # 尝试查找包含城市名称的结果（优先查找带"城市"标签的）
                # 使用清理后的城市名称
                result = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{cleaned_city_name}").textContains("城市")')
                if result:
                    print(f"✅ 搜索结果已出现（带城市标签）")
                    return True
            except NoSuchElementException:
                try:
                    # 尝试查找包含城市名称的结果（不带标签的）
                    # 使用清理后的城市名称
                    result = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{cleaned_city_name}")')
                    if result:
                        print(f"✅ 搜索结果已出现")
                        return True
                except NoSuchElementException:
                    if i < max_wait - 1:
                        wait_step(driver, 0.5)
                    else:
                        print("⚠️ 搜索结果未出现，但继续执行...")
                        return True
        
        return True
        
    except Exception as e:
        print(f"❌ 输入搜索内容失败: {e}")
        return False



def select_city_from_results(driver, city_name):
    """从搜索结果中选择目标城市

    优先选择：
    1. 精确匹配的城市名称
    2. 包含城市名称但不包含"站"、"机场"等后缀的城市
    3. 带有"城市"标签的城市
    4. 其他包含城市名称的结果
    """
    # 清理和验证城市名称，确保与输入时使用的名称一致
    cleaned_city_name = _clean_city_name(city_name)
    
    if not cleaned_city_name:
        print(f"❌ 城市名称无效或为空: {city_name}")
        return False
    
    print(f"\n🎯 步骤: 从搜索结果中选择城市 '{cleaned_city_name}'")
    
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            # 策略0：优先查找"城市（不限站点）"选项（主导策略）
            try:
                # 先尝试查找包含"不限站点"的选项
                city_element = None
                city_text = None
                
                # 方法1: 查找包含"不限站点"的文本
                try:
                    city_element = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{cleaned_city_name}").textContains("不限站点")')
                    city_text = city_element.text
                    print(f"✅ 找到'不限站点'选项: {city_text}")
                except NoSuchElementException:
                    # 方法2: 查找包含"城市"和"不限"的文本
                    try:
                        city_element = driver.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().textContains("{cleaned_city_name}").textContains("城市").textContains("不限")')
                        city_text = city_element.text
                        print(f"✅ 找到'城市不限'选项: {city_text}")
                    except NoSuchElementException:
                        # 方法3: 查找包含"城市"和"("的文本（可能是"城市（不限站点）"）
                        try:
                            all_city_elements = driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                f'new UiSelector().textContains("{cleaned_city_name}").textContains("城市")')
                            for elem in all_city_elements:
                                try:
                                    text = elem.text
                                    if "(" in text or "不限" in text or "站点" in text:
                                        city_element = elem
                                        city_text = text
                                        print(f"✅ 找到可能的'城市（不限站点）'选项: {text}")
                                        break
                                except:
                                    pass
                        except:
                            pass
                
                if city_element and city_text:
                    # 调试信息：显示元素详情
                    try:
                        element_text = city_element.text
                        element_location = city_element.location
                        element_size = city_element.size
                        print(f"🔍 策略0找到元素:")
                        print(f"   文本: {element_text}")
                        print(f"   位置: {element_location}")
                        print(f"   大小: {element_size}")
                    except Exception as debug_error:
                        print(f"⚠️ 无法获取元素详情: {debug_error}")
                    
                    # 尝试点击 - 优先使用tap方法
                    try:
                        location = city_element.location
                        size = city_element.size
                        center_x = location['x'] + size['width'] // 2
                        center_y = location['y'] + size['height'] // 2
                        print(f"   使用tap点击: ({center_x}, {center_y})")
                        driver.tap([(center_x, center_y)], 100)
                        print(f"✅ 已使用tap点击城市元素（不限站点）: {city_text} ({center_x}, {center_y})")
                    except Exception as tap_error:
                        print(f"⚠️ tap()失败: {tap_error}，尝试使用click方法...")
                        # 备用方法：使用click
                        try:
                            city_element.click()
                            print(f"✅ 已使用click点击城市元素（不限站点）: {city_text}")
                        except Exception as click_error:
                            print(f"❌ click也失败: {click_error}")
                            raise
                    
                    wait_step(driver, 3)  # 增加等待时间，确保选择生效
                    print(f"✅ 成功选择城市（不限站点）: {city_text}")
                    
                    # 验证是否返回到主页面
                    if verify_returned_to_main_page(driver):
                        print("✅ 已返回到主页面")
                        # 额外验证：检查城市是否真的被选择
                        try:
                            page_source = driver.page_source
                            if cleaned_city_name in page_source:
                                print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                            else:
                                print(f"⚠️ 警告：城市 '{cleaned_city_name}' 未在主页面中找到，可能选择未生效")
                        except:
                            pass
                        return True
                    else:
                        print("⚠️ 未自动返回主页面，尝试按返回键...")
                        try:
                            driver.back()
                            wait_step(driver, 3)  # 增加等待时间
                            if verify_returned_to_main_page(driver):
                                print("✅ 已通过返回键返回到主页面")
                                # 验证城市是否被选择
                                try:
                                    page_source = driver.page_source
                                    if cleaned_city_name in page_source:
                                        print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                                except:
                                    pass
                                return True
                        except Exception as e:
                            print(f"⚠️ 按返回键失败: {e}")
                        return True  # 即使验证失败也返回True，让后续流程继续
            except NoSuchElementException:
                pass
            
            # 策略1：查找带"城市"标签的结果（备用策略，仅按城市名称，不包含"不限站点"）
            try:
                # 查找所有带"城市"标签的结果，然后过滤掉包含"不限站点"的
                all_city_elements = driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{cleaned_city_name}").textContains("城市")')
                
                city_element = None
                city_text = None
                
                # 过滤掉包含"不限站点"、"不限"、"站点"的选项
                for elem in all_city_elements:
                    try:
                        text = elem.text
                        # 排除包含"不限站点"相关文字的选项（这些已经在策略0中处理）
                        if "不限站点" not in text and "不限" not in text and "站点" not in text:
                            city_element = elem
                            city_text = text
                            print(f"✅ 找到带'城市'标签的选项（不含不限站点）: {text}")
                            break
                    except:
                        pass
                
                if not city_element and all_city_elements:
                    # 如果过滤后没有结果，使用第一个（可能是"城市（不限站点）"，但策略0已经失败）
                    city_element = all_city_elements[0]
                    try:
                        city_text = city_element.text
                        print(f"⚠️ 所有选项都包含'不限站点'，使用第一个选项: {city_text}")
                    except:
                        city_text = cleaned_city_name
                
                if city_element:
                    # 调试信息：显示元素详情
                    try:
                        element_text = city_element.text
                        element_location = city_element.location
                        element_size = city_element.size
                        print(f"🔍 策略1找到元素:")
                        print(f"   文本: {element_text}")
                        print(f"   位置: {element_location}")
                        print(f"   大小: {element_size}")
                    except Exception as debug_error:
                        print(f"⚠️ 无法获取元素详情: {debug_error}")
                    
                    # 尝试点击 - 优先使用tap方法
                    try:
                        location = city_element.location
                        size = city_element.size
                        center_x = location['x'] + size['width'] // 2
                        center_y = location['y'] + size['height'] // 2
                        print(f"   使用tap点击: ({center_x}, {center_y})")
                        driver.tap([(center_x, center_y)], 100)
                        print(f"✅ 已使用tap点击城市元素（带城市标签）: {city_text or cleaned_city_name} ({center_x}, {center_y})")
                    except Exception as tap_error:
                        print(f"⚠️ tap()失败: {tap_error}，尝试使用click方法...")
                        # 备用方法：使用click
                        try:
                            city_element.click()
                            print(f"✅ 已使用click点击城市元素（带城市标签）: {city_text or cleaned_city_name}")
                        except Exception as click_error:
                            print(f"❌ click也失败: {click_error}")
                            raise
                
                wait_step(driver, 3)  # 增加等待时间，确保选择生效
                print(f"✅ 成功选择城市（带城市标签）: {cleaned_city_name}")
                
                # 验证是否返回到主页面
                if verify_returned_to_main_page(driver):
                    print("✅ 已返回到主页面")
                    # 额外验证：检查城市是否真的被选择
                    try:
                        page_source = driver.page_source
                        if cleaned_city_name in page_source:
                            print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                        else:
                            print(f"⚠️ 警告：城市 '{cleaned_city_name}' 未在主页面中找到，可能选择未生效")
                    except:
                        pass
                    return True
                else:
                    print("⚠️ 未自动返回主页面，尝试按返回键...")
                    try:
                        driver.back()
                        wait_step(driver, 3)  # 增加等待时间
                        if verify_returned_to_main_page(driver):
                            print("✅ 已通过返回键返回到主页面")
                            # 验证城市是否被选择
                            try:
                                page_source = driver.page_source
                                if cleaned_city_name in page_source:
                                    print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                            except:
                                pass
                            return True
                    except Exception as e:
                        print(f"⚠️ 按返回键失败: {e}")
                    return True  # 即使验证失败也返回True，让后续流程继续
            except NoSuchElementException:
                pass
            
            # 策略2：精确匹配（作为备选）
            try:
                city_element = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{cleaned_city_name}")')
                
                # 调试信息：显示元素详情
                try:
                    element_text = city_element.text
                    element_location = city_element.location
                    element_size = city_element.size
                    print(f"🔍 策略2找到元素:")
                    print(f"   文本: {element_text}")
                    print(f"   位置: {element_location}")
                    print(f"   大小: {element_size}")
                except Exception as debug_error:
                    print(f"⚠️ 无法获取元素详情: {debug_error}")
                
                # 尝试点击 - 优先使用tap方法
                try:
                    location = city_element.location
                    size = city_element.size
                    center_x = location['x'] + size['width'] // 2
                    center_y = location['y'] + size['height'] // 2
                    print(f"   使用tap点击: ({center_x}, {center_y})")
                    driver.tap([(center_x, center_y)], 100)
                    print(f"✅ 已使用tap点击城市元素: {cleaned_city_name} ({center_x}, {center_y})")
                except Exception as tap_error:
                    print(f"⚠️ tap()失败: {tap_error}，尝试使用click方法...")
                    # 备用方法：使用click
                    try:
                        city_element.click()
                        print(f"✅ 已使用click点击城市元素: {cleaned_city_name}")
                    except Exception as click_error:
                        print(f"❌ click也失败: {click_error}")
                        raise
                
                wait_step(driver, 3)  # 增加等待时间，确保选择生效
                print(f"✅ 成功选择城市: {cleaned_city_name}")
                
                # 验证是否返回到主页面
                if verify_returned_to_main_page(driver):
                    print("✅ 已返回到主页面")
                    # 额外验证：检查城市是否真的被选择
                    try:
                        page_source = driver.page_source
                        if cleaned_city_name in page_source:
                            print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                        else:
                            print(f"⚠️ 警告：城市 '{cleaned_city_name}' 未在主页面中找到，可能选择未生效")
                    except:
                        pass
                    return True
                else:
                    print("⚠️ 未自动返回主页面，尝试按返回键...")
                    try:
                        driver.back()
                        wait_step(driver, 3)  # 增加等待时间
                        if verify_returned_to_main_page(driver):
                            print("✅ 已通过返回键返回到主页面")
                            # 验证城市是否被选择
                            try:
                                page_source = driver.page_source
                                if cleaned_city_name in page_source:
                                    print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                            except:
                                pass
                            return True
                    except Exception as e:
                        print(f"⚠️ 按返回键失败: {e}")
                    return True  # 即使验证失败也返回True，让后续流程继续
            except NoSuchElementException:
                pass
            
            # 策略3：从页面源码中查找所有包含城市名称的元素，优先选择带"城市"标签的
            try:
                page_source = driver.page_source
                root = etree.fromstring(page_source.encode('utf-8'))
                xpath_query = f'.//*[contains(@text, "{cleaned_city_name}")]'
                elements = root.xpath(xpath_query)
                
                # 收集所有候选城市
                candidates = []
                for elem in elements:
                    text = elem.get('text', '').strip()
                    if cleaned_city_name in text:
                        # 检查是否包含"城市"标签（最优先）
                        has_city_label = '城市' in text or 'city' in text.lower()
                        # 检查是否包含后缀（不优先）
                        has_suffix = any(
                            suffix in text for suffix in [
                                '站', '机场', '火车站', '机场站', 'Station', 'Airport'])
                        # 检查是否是精确匹配（使用清理后的名称）
                        is_exact = text == cleaned_city_name

                        candidates.append({
                            'text': text,
                            'element': elem,
                            'is_exact': is_exact,
                            'has_city_label': has_city_label,
                            'has_suffix': has_suffix,
                            # 优先级：有城市标签 > 精确匹配 > 无后缀
                            'priority': (has_city_label, is_exact, not has_suffix)
                        })

                # 按优先级排序：有城市标签 > 精确匹配 > 无后缀
                candidates.sort(
                    key=lambda x: (
                        x['priority'][0],
                        x['priority'][1],
                        x['priority'][2]),
                    reverse=True)

                # 尝试选择优先级最高的候选城市
                for candidate in candidates:
                    try:
                        city_element = driver.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{candidate["text"]}")')
                        
                        # 尝试点击 - 优先使用tap方法
                        try:
                            location = city_element.location
                            size = city_element.size
                            center_x = location['x'] + size['width'] // 2
                            center_y = location['y'] + size['height'] // 2
                            print(f"   使用tap点击: ({center_x}, {center_y})")
                            driver.tap([(center_x, center_y)], 100)
                            print(f"✅ 已使用tap点击城市元素: {candidate['text']} ({center_x}, {center_y})")
                        except Exception as tap_error:
                            print(f"⚠️ tap()失败: {tap_error}，尝试使用click方法...")
                            # 备用方法：使用click
                            try:
                                city_element.click()
                                print(f"✅ 已使用click点击城市元素: {candidate['text']}")
                            except Exception as click_error:
                                print(f"❌ click也失败: {click_error}")
                                continue
                        
                        reason = []
                        if candidate['has_city_label']:
                            reason.append('带城市标签')
                        if candidate['is_exact']:
                            reason.append('精确匹配')
                        if not candidate['has_suffix']:
                            reason.append('无后缀')
                        print(
                            f"✅ 成功选择城市（通过页面源码，{'、'.join(reason) if reason else '匹配'}）: {candidate['text']}")
                        wait_step(driver, 3)  # 增加等待时间，确保选择生效
                        
                        # 验证是否返回到主页面
                        if verify_returned_to_main_page(driver):
                            print("✅ 已返回到主页面")
                            # 额外验证：检查城市是否真的被选择
                            try:
                                page_source = driver.page_source
                                candidate_text = candidate['text']
                                if cleaned_city_name in page_source or candidate_text in page_source:
                                    print(f"✅ 城市 '{candidate_text}' 已成功选择并带回主页面")
                                else:
                                    print(f"⚠️ 警告：城市 '{candidate_text}' 未在主页面中找到，可能选择未生效")
                            except:
                                pass
                            return True
                        else:
                            print("⚠️ 未自动返回主页面，尝试按返回键...")
                            try:
                                driver.back()
                                wait_step(driver, 3)  # 增加等待时间
                                if verify_returned_to_main_page(driver):
                                    print("✅ 已通过返回键返回到主页面")
                                    # 验证城市是否被选择
                                    try:
                                        page_source = driver.page_source
                                        candidate_text = candidate['text']
                                        if cleaned_city_name in page_source or candidate_text in page_source:
                                            print(f"✅ 城市 '{candidate_text}' 已成功选择并带回主页面")
                                    except:
                                        pass
                                    return True
                            except Exception as e:
                                print(f"⚠️ 按返回键失败: {e}")
                        return True  # 即使验证失败也返回True，让后续流程继续
            
                    except BaseException:
                        continue

                # 如果上面的候选城市都失败，尝试使用textContains作为最后手段
                try:
                    city_element = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{cleaned_city_name}")')
                    
                    # 尝试点击 - 优先使用tap方法
                    try:
                        location = city_element.location
                        size = city_element.size
                        center_x = location['x'] + size['width'] // 2
                        center_y = location['y'] + size['height'] // 2
                        print(f"   使用tap点击: ({center_x}, {center_y})")
                        driver.tap([(center_x, center_y)], 100)
                        print(f"✅ 已使用tap点击城市元素（通过textContains）: {cleaned_city_name} ({center_x}, {center_y})")
                    except Exception as tap_error:
                        print(f"⚠️ tap()失败: {tap_error}，尝试使用click方法...")
                        # 备用方法：使用click
                        try:
                            city_element.click()
                            print(f"✅ 已使用click点击城市元素（通过textContains）: {cleaned_city_name}")
                        except Exception as click_error:
                            print(f"❌ click也失败: {click_error}")
                            raise
                    
                    wait_step(driver, 3)  # 增加等待时间，确保选择生效
                    print(f"✅ 成功选择城市（通过textContains）: {cleaned_city_name}")
                    
                    # 验证是否返回到主页面
                    if verify_returned_to_main_page(driver):
                        print("✅ 已返回到主页面")
                        # 额外验证：检查城市是否真的被选择
                        try:
                            page_source = driver.page_source
                            if cleaned_city_name in page_source:
                                print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                            else:
                                print(f"⚠️ 警告：城市 '{cleaned_city_name}' 未在主页面中找到，可能选择未生效")
                        except:
                            pass
                        return True
                    else:
                        print("⚠️ 未自动返回主页面，尝试按返回键...")
                        try:
                            driver.back()
                            wait_step(driver, 3)  # 增加等待时间
                            if verify_returned_to_main_page(driver):
                                print("✅ 已通过返回键返回到主页面")
                                # 验证城市是否被选择
                                try:
                                    page_source = driver.page_source
                                    if cleaned_city_name in page_source:
                                        print(f"✅ 城市 '{cleaned_city_name}' 已成功选择并带回主页面")
                                except:
                                    pass
                                return True
                        except Exception as e:
                            print(f"⚠️ 按返回键失败: {e}")
                    return True  # 即使验证失败也返回True，让后续流程继续
                except NoSuchElementException:
                    pass
            except Exception as e:
                print(f"⚠️ 策略3失败: {e}")
                pass
            
            if attempt < max_attempts:
                print(f"⚠️ 第{attempt}次尝试未找到城市，等待后重试...")
                wait_step(driver, 1)
            else:
                print(f"❌ 尝试{max_attempts}次后仍未找到城市: {cleaned_city_name}")
                return False
                
        except Exception as e:
            print(f"❌ 选择城市时出错: {e}")
            if attempt >= max_attempts:
                return False
            wait_step(driver, 1)
    
    return False



def get_current_page_settings(driver):
    """
    获取当前空铁联运页面显示的出发城市、到达城市和日期
    
    Returns:
        dict: {'from_city': str, 'to_city': str, 'date': str}
    """
    print("\n🔍 检查当前页面显示的城市和日期...")
    
    result = {'from_city': None, 'to_city': None, 'date': None}
    
    try:
        page_source = driver.page_source
        root = etree.fromstring(page_source.encode('utf-8'))
        import re
        
        # 扩大搜索范围：查找所有可能的元素类型（TextView, EditText, Button等）
        all_elements = root.xpath('.//*[@text]')
        city_elements = []
        
        screen_size = driver.get_window_size()
        screen_height = screen_size.get('height', 2400)

        # 扩大y坐标范围：从400到900（原来500-800可能太严格）
        y_min = 400
        y_max = min(900, screen_height * 0.4)

        for elem in all_elements:
            text = elem.get('text', '').strip()
            bounds = elem.get('bounds', '')
            
            if not text or not bounds:
                continue
                
            try:
                match = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # 城市元素：2-4个中文字符，y坐标在扩大后的范围内
                    if 2 <= len(text) <= 4 and all(
                            '\u4e00' <= c <= '\u9fff' for c in text):
                        if y_min <= center_y <= y_max and 50 <= center_x <= 1000:
                            city_elements.append({
                                'text': text,
                                'center_x': center_x,
                                'center_y': center_y,
                                'bounds': bounds
                            })
                            print(
                                f"🔍 找到候选城市元素: {text}, 位置: {bounds}, 中心: ({center_x}, {center_y})")
                    
                    # 日期元素：包含"月"和"日"
                    if '月' in text and '日' in text:
                        result['date'] = text
                        print(f"📅 当前日期: {text}")
            except BaseException:

                pass

        # 优先使用标签（"出发"、"到达"）来区分城市，而不是依赖x坐标
        # 策略1：查找包含"出发"或"到达"标签的元素，然后在其附近查找城市
        city_label_keywords = {
            'from': ['出发', 'from', 'departure', 'depart'],
            'to': ['到达', 'to', 'arrival', 'arrive', 'destination']
        }

        from_city_elem = None
        to_city_elem = None

        # 查找"出发"标签附近的城市
        for keyword in city_label_keywords['from']:
            label_xpath = f'.//*[contains(@text, "{keyword}") or contains(@content-desc, "{keyword}") or contains(@resource-id, "{keyword}")]'
            label_elements = root.xpath(label_xpath)
            for label_elem in label_elements:
                label_bounds = label_elem.get('bounds', '')
                if not label_bounds:
                    continue
                try:
                    match = re.search(
                        r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', label_bounds)
                    if match:
                        label_x1, label_y1, label_x2, label_y2 = map(
                            int, match.groups())
                        label_center_x = (label_x1 + label_x2) // 2
                        label_center_y = (label_y1 + label_y2) // 2

                        # 在标签附近查找城市元素
                        for city_elem in city_elements:
                            city_center_x = city_elem['center_x']
                            city_center_y = city_elem['center_y']
                            # 检查城市元素是否在标签附近（同一行，y坐标相近，x坐标在标签右侧）
                            if abs(
                                    city_center_y - label_center_y) < 100 and city_center_x > label_center_x - 50:
                                from_city_elem = city_elem
                                print(f"✅ 通过'出发'标签找到出发城市: {city_elem['text']}")
                                break
                        if from_city_elem:
                            break
                except BaseException:

                    pass
            if from_city_elem:
                break

        # 查找"到达"标签附近的城市
        for keyword in city_label_keywords['to']:
            label_xpath = f'.//*[contains(@text, "{keyword}") or contains(@content-desc, "{keyword}") or contains(@resource-id, "{keyword}")]'
            label_elements = root.xpath(label_xpath)
            for label_elem in label_elements:
                label_bounds = label_elem.get('bounds', '')
                if not label_bounds:
                    continue
                try:
                    match = re.search(
                        r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', label_bounds)
                    if match:
                        label_x1, label_y1, label_x2, label_y2 = map(
                            int, match.groups())
                        label_center_x = (label_x1 + label_x2) // 2
                        label_center_y = (label_y1 + label_y2) // 2

                        # 在标签附近查找城市元素
                        for city_elem in city_elements:
                            city_center_x = city_elem['center_x']
                            city_center_y = city_elem['center_y']
                            # 检查城市元素是否在标签附近（同一行，y坐标相近，x坐标在标签右侧）
                            if abs(
                                    city_center_y - label_center_y) < 100 and city_center_x > label_center_x - 50:
                                to_city_elem = city_elem
                                print(f"✅ 通过'到达'标签找到到达城市: {city_elem['text']}")
                                break
                        if to_city_elem:
                            break
                except BaseException:

                    pass
            if to_city_elem:
                break

        # 如果通过标签找到了城市，使用标签结果
        if from_city_elem:
            result['from_city'] = from_city_elem['text']
            print(f"🏙️ 当前出发城市: {result['from_city']}")
        if to_city_elem:
            result['to_city'] = to_city_elem['text']
            print(f"🏙️ 当前到达城市: {result['to_city']}")

        # 策略2：如果标签方法失败，使用x坐标作为最后手段
        if not from_city_elem or not to_city_elem:
            if city_elements:
                # 按x坐标排序（从小到大）
                city_elements.sort(key=lambda x: x['center_x'])
                print(f"📊 找到 {len(city_elements)} 个候选城市元素")
                city_elements.sort(key=lambda x: x['center_x'])
                # 左侧的是出发城市（x坐标最小）
                city_elements.sort(key=lambda x: x['center_x'])
                result['from_city'] = city_elements[0]['text']
                print(f"⚠️ 使用位置筛选（最后手段）识别出发城市: {result['from_city']}")
            
                # 右侧的是到达城市（x坐标最大）
                if not to_city_elem and len(city_elements) >= 2:
                    result['to_city'] = city_elements[-1]['text']
                    print(f"⚠️ 使用位置筛选（最后手段）识别到达城市: {result['to_city']}")
        else:
                    print(f"⚠️ 未找到城市元素，尝试查找可点击的元素...")
                    # 备用方案：查找可点击的元素
                    clickable_elements = root.xpath(
                    './/*[@clickable="true" and @text]')
                    for elem in clickable_elements:
                        text = elem.get('text', '').strip()
                        bounds = elem.get('bounds', '')
                        if text and bounds:
                            try:
                                match = re.search(
                                r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                                if match:
                                    x1, y1, x2, y2 = map(int, match.groups())
                                    center_x = (x1 + x2) // 2
                                    center_y = (y1 + y2) // 2
                                    if y_min <= center_y <= y_max and 50 <= center_x <= 1000:
                                        print(f"🔍 找到可点击元素: {text}, 位置: {bounds}")
                            except BaseException:

                                    pass
        
    except Exception as e:


        print(f"⚠️ 获取当前页面设置失败: {e}")
        import traceback
        traceback.print_exc()
    
    return result



def step4a_select_from_city(driver, from_city, max_retries=2):
    """
    步骤4A: 选择出发城市（仅在需要时修改）
    
    Args:
        driver: WebDriver实例
        from_city: 目标出发城市名称
    
    Returns:
        bool: 是否成功
    """
    if not from_city:
        print("ℹ️ 未提供出发城市，跳过选择")
        return True
    
    print(f"\n🏙️ 步骤4A: 检查出发城市 (目标: {from_city}, 最大重试: {max_retries})")

    # 防止死循环：如果已经重试过，直接返回失败
    if max_retries <= 0:
        print(f"⚠️ 已达到最大重试次数，停止修改出发城市，避免死循环")
        return False
    
    # 获取当前页面显示的出发城市
    current_settings = get_current_page_settings(driver)
    current_from_city = current_settings.get('from_city')
    
    # 检查是否需要修改
    if current_from_city == from_city:
        print(f"✅ 出发城市已是 {from_city}，无需修改")
        return True
    
    print(f"🔄 需要将出发城市从 {current_from_city} 修改为 {from_city}")
    
    if not click_city_and_enter_selection(driver, '出发', current_from_city):
        print("❌ 无法进入城市选择页面")
        return False
    
    if not input_city_search(driver, from_city):
        print("❌ 无法输入搜索内容")
        return False
    
    if not select_city_from_results(driver, from_city):
        print("❌ 无法选择城市")
        return False
    
    # 选择城市后，验证是否返回到主页面
    print(f"✅ 出发城市已选择: {from_city}")
    wait_step(driver, 2)  # 等待页面稳定
    
    # 验证是否返回到主页面
    if not verify_returned_to_main_page(driver):
        print("⚠️ 选择出发城市后未返回到主页面，尝试按返回键...")
        try:
            driver.back()
            wait_step(driver, 2)
        except Exception as e:
            print(f"⚠️ 按返回键失败: {e}")
    
    print(f"✅ 出发城市已修改为 {from_city}")

    # 验证修改后的城市设置（可能需要多次验证，因为APP可能需要时间更新）
    max_verify_attempts = 3
    for attempt in range(1, max_verify_attempts + 1):
        current_settings = get_current_page_settings(driver)
        final_from_city = current_settings.get('from_city')
        final_to_city = current_settings.get('to_city')
        print(
            f"🔍 验证最终城市设置 (尝试 {attempt}/{max_verify_attempts}): 出发城市={final_from_city}, 到达城市={final_to_city}")

        # 如果出发城市正确，直接返回成功（不检查到达城市，因为可能还未设置）
        if final_from_city == from_city:
            print(f"✅ 出发城市设置正确: {final_from_city}")
    return True

    # 如果还有尝试机会，等待后重试
    if attempt < max_verify_attempts:
        wait_step(driver, 1)

    # 如果验证失败，检查是否需要重试
    print(f"⚠️ 警告：出发城市设置可能不正确。预期: {from_city}, 实际: {final_from_city}")

    # 如果当前城市与目标城市不同，且还有重试机会，尝试重试
    if final_from_city != from_city and max_retries > 0:
        print(f"🔄 重试设置出发城市 (剩余重试: {max_retries})...")
        return step4a_select_from_city(driver, from_city, max_retries - 1)

    return False



def step4b_select_to_city(driver, to_city, max_retries=2):
    """
    步骤4B: 选择到达城市（仅在需要时修改）
    
    Args:
        driver: WebDriver实例
        to_city: 目标到达城市名称
        max_retries: 最大重试次数，防止死循环
    
    Returns:
        bool: 是否成功
    """
    if not to_city:
        print("ℹ️ 未提供到达城市，跳过选择")
        return True
    
    print(f"\n🏙️ 步骤4B: 检查到达城市 (目标: {to_city}, 最大重试: {max_retries})")
    
    # 获取当前页面显示的到达城市
    current_settings = get_current_page_settings(driver)
    current_to_city = current_settings.get('to_city')
    
    # 检查是否需要修改
    if current_to_city == to_city:
        print(f"✅ 到达城市已是 {to_city}，无需修改")
        return True
    
    # 防止死循环：如果已经重试过，直接返回失败
    if max_retries <= 0:
        print(f"⚠️ 已达到最大重试次数，停止修改到达城市，避免死循环")
        return False
    
    print(f"🔄 需要将到达城市从 {current_to_city} 修改为 {to_city}")

    # 重要：在选择到达城市之前，先验证当前页面状态，确保出发城市没有被误操作
    pre_settings = get_current_page_settings(driver)
    pre_from_city = pre_settings.get('from_city')
    pre_to_city = pre_settings.get('to_city')
    print(f"🔍 选择到达城市前的页面状态: 出发城市={pre_from_city}, 到达城市={pre_to_city}")
    
    if not click_city_and_enter_selection(driver, '到达', current_to_city):
        print("❌ 无法进入城市选择页面")
        return False
    
    if not input_city_search(driver, to_city):
        print("❌ 无法输入搜索内容")
        return False
    
    if not select_city_from_results(driver, to_city):
        print("❌ 无法选择城市")
        return False
    
    # 选择城市后，验证是否返回到主页面
    print(f"✅ 到达城市已选择: {to_city}")
    wait_step(driver, 2)  # 等待页面稳定
    
    # 验证是否返回到主页面
    if not verify_returned_to_main_page(driver):
        print("⚠️ 选择到达城市后未返回到主页面，尝试按返回键...")
        try:
            driver.back()
            wait_step(driver, 2)
        except Exception as e:
            print(f"⚠️ 按返回键失败: {e}")
    
    print(f"✅ 到达城市已修改为 {to_city}")

    # 验证修改后的城市设置（可能需要多次验证，因为APP可能需要时间更新）
    max_verify_attempts = 3
    for attempt in range(1, max_verify_attempts + 1):
        current_settings = get_current_page_settings(driver)
        final_from_city = current_settings.get('from_city')
        final_to_city = current_settings.get('to_city')
        print(
            f"🔍 验证最终城市设置 (尝试 {attempt}/{max_verify_attempts}): 出发城市={final_from_city}, 到达城市={final_to_city}")

        # 如果两个城市都正确，直接返回成功
        if final_from_city == pre_from_city and final_to_city == to_city:
            print(f"✅ 城市设置正确：出发={final_from_city}, 到达={final_to_city}")
    return True

    # 如果还有尝试机会，等待后重试
    if attempt < max_verify_attempts:
        wait_step(driver, 1)

    # 如果验证失败，尝试修复
    print(f"⚠️ 城市设置验证失败，尝试修复...")

    # 情况1：出发城市被意外修改，但到达城市正确
    if final_from_city != pre_from_city and final_to_city == to_city:
        print(f"⚠️ 警告：出发城市被意外修改！原值: {pre_from_city}, 当前值: {final_from_city}")
        print(f"🔄 需要重新设置出发城市为: {pre_from_city}")
        # 重新设置出发城市（传递剩余重试次数，防止死循环）
        if not step4a_select_from_city(driver, pre_from_city, max_retries=1):
            print(f"❌ 重新设置出发城市失败")
            return False
        # 再次验证
        wait_step(driver, 2)
        current_settings = get_current_page_settings(driver)
        if current_settings.get('from_city') == pre_from_city and current_settings.get(
                'to_city') == to_city:
            print(f"✅ 修复成功：出发={pre_from_city}, 到达={to_city}")
            return True

    # 情况2：到达城市不正确，但出发城市正确
    elif final_from_city == pre_from_city and final_to_city != to_city:
        print(f"⚠️ 警告：到达城市设置不正确！预期: {to_city}, 实际: {final_to_city}")
        # 如果到达城市未改变，可能是APP交换了城市，需要重新设置
        if final_to_city == pre_from_city:
            print(f"⚠️ 检测到城市可能被交换，重新设置到达城市...")
            # 重新设置到达城市（传递剩余重试次数，防止死循环）
            if not step4b_select_to_city(driver, to_city, max_retries=1):
                print(f"❌ 重新设置到达城市失败")
                return False
        else:
            print(f"⚠️ 到达城市未改变，可能需要重新尝试")

    # 情况3：两个城市都不正确（可能被交换）
    elif final_from_city != pre_from_city and final_to_city != to_city:
        print(f"⚠️ 警告：两个城市都被修改！可能发生了城市交换")
        print(f"   原状态: 出发={pre_from_city}, 到达={pre_to_city}")
        print(f"   当前状态: 出发={final_from_city}, 到达={final_to_city}")
        print(f"   目标状态: 出发={pre_from_city}, 到达={to_city}")

        # 情况3a：检测到完全交换（出发=原到达，到达=原出发）
        if final_from_city == pre_to_city and final_to_city == pre_from_city:
            print(f"🔄 检测到完全城市交换，重新设置两个城市...")
            # 先设置出发城市（传递剩余重试次数，防止死循环）
            if not step4a_select_from_city(
                    driver, pre_from_city, max_retries=1):
                print(f"❌ 重新设置出发城市失败")
                return False
            wait_step(driver, 2)
            # 再设置到达城市（传递剩余重试次数，防止死循环）
            if not step4b_select_to_city(driver, to_city, max_retries=1):
                print(f"❌ 重新设置到达城市失败")
                return False
        # 情况3b：选择的到达城市被放到了出发位置（出发=选择的到达城市，到达=原出发城市）
        elif final_from_city == to_city and final_to_city == pre_from_city:
            print(f"🔄 检测到选择的到达城市被放到了出发位置，重新设置两个城市...")
            # 先设置出发城市为正确的值（传递剩余重试次数，防止死循环）
            if not step4a_select_from_city(
                    driver, pre_from_city, max_retries=1):
                print(f"❌ 重新设置出发城市失败")
                return False
            wait_step(driver, 2)
            # 再设置到达城市为正确的值（传递剩余重试次数，防止死循环）
            if not step4b_select_to_city(driver, to_city, max_retries=1):
                print(f"❌ 重新设置到达城市失败")
                return False
        # 情况3c：其他情况，直接重新设置两个城市
        else:
            print(f"🔄 检测到城市设置异常，重新设置两个城市...")
            # 先设置出发城市（传递剩余重试次数，防止死循环）
            if not step4a_select_from_city(
                    driver, pre_from_city, max_retries=1):
                print(f"❌ 重新设置出发城市失败")
                return False
            wait_step(driver, 2)
            # 再设置到达城市（传递剩余重试次数，防止死循环）
            if not step4b_select_to_city(driver, to_city, max_retries=1):
                print(f"❌ 重新设置到达城市失败")
                return False

    # 最终验证
    wait_step(driver, 2)
    final_settings = get_current_page_settings(driver)
    if final_settings.get('from_city') == pre_from_city and final_settings.get(
            'to_city') == to_city:
        print(f"✅ 最终验证通过：出发={pre_from_city}, 到达={to_city}")
        return True
    else:
        print(
            f"⚠️ 最终验证失败：出发={final_settings.get('from_city')}, 到达={final_settings.get('to_city')}")
        return False

