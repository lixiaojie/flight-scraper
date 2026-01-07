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

def tprint(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}]", *args, **kwargs)


def wait_step(driver, seconds=2):
    """步骤间等待"""
    print(f"⏳ 等待 {seconds} 秒...")
    time.sleep(seconds)


def parse_bounds(bounds_str):
    """解析bounds字符串，返回(x1, y1, x2, y2)"""
    try:
        match = re.search(
            r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            return tuple(map(int, match.groups()))
    except BaseException:
        pass
    return None
