# -*- coding: utf-8 -*-
# 主入口文件 - 导入所有模块并提供统一接口

# 导入所有模块
from utils import tprint, wait_step, parse_bounds
from scroll_utils import (
    find_scrollable_list,
    swipe_down_in_middle,
    swipe_up_in_middle,
    scroll_to_top,
    perform_scroll_forward,
    perform_scroll_backward,
    perform_scroll_swipe,
    perform_scroll,
    smart_scroll_and_capture
)
from capture_utils import extract_flight_elements_from_xml
from date_selection import step4c_select_date
from city_selection import (
    get_city_pinyin_initials,
    find_city_element,
    click_city_and_enter_selection,
    find_city_search_box,
    input_city_search,
    select_city_from_results,
    step4a_select_from_city,
    step4b_select_to_city,
    get_current_page_settings
)
from navigation import (
    launch_12306_app,
    step2_check_homepage,
    step3_click_air_rail_transfer,
    step4_check_air_rail_page,
    step5_click_search,
    step6_check_flight_list,
    navigate_and_search
)

# 重新导出所有函数，保持向后兼容
__all__ = [
    'tprint',
    'wait_step',
    'parse_bounds',
    'find_scrollable_list',
    'swipe_down_in_middle',
    'swipe_up_in_middle',
    'scroll_to_top',
    'perform_scroll_forward',
    'perform_scroll_backward',
    'perform_scroll_swipe',
    'perform_scroll',
    'smart_scroll_and_capture',
    'extract_flight_elements_from_xml',
    'step4c_select_date',
    'get_city_pinyin_initials',
    'find_city_element',
    'click_city_and_enter_selection',
    'find_city_search_box',
    'input_city_search',
    'select_city_from_results',
    'step4a_select_from_city',
    'step4b_select_to_city',
    'get_current_page_settings',
    'launch_12306_app',
    'step2_check_homepage',
    'step3_click_air_rail_transfer',
    'step4_check_air_rail_page',
    'step5_click_search',
    'step6_check_flight_list',
    'navigate_and_search',
]
