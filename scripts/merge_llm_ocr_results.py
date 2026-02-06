#!/usr/bin/env python3
"""
合并大模型和OCR识别结果
优先使用大模型结果，缺失字段从OCR结果补充，并标记字段来源
"""
import json
from typing import List, Dict, Any, Set


def merge_llm_ocr_results(llm_flights: List[Dict[str, Any]], 
                          ocr_flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并大模型和OCR识别结果
    
    Args:
        llm_flights: 大模型API识别结果
        ocr_flights: OCR方法识别结果
    
    Returns:
        合并后的航班列表，每个航班包含field_sources字段标识哪些字段来自OCR
    """
    if not llm_flights:
        # 如果大模型没有结果，全部使用OCR，标记所有字段来自OCR
        for flight in ocr_flights:
            # 标记所有字段来自OCR
            ocr_fields = {
                'airline', 'flight_number', 'departure_time', 'arrival_time',
                'departure_airport', 'arrival_airport', 'price', 'discount_rate',
                'cabin_class', 'aircraft_type', 'flight_duration',
                'has_stopover', 'stopover_city', 'is_shared_flight'
            }
            flight['field_sources'] = json.dumps({field: 'ocr' for field in ocr_fields if flight.get(field)})
        return ocr_flights
    
    # 按航班号建立OCR结果索引
    ocr_flight_map = {}
    for ocr_flight in ocr_flights:
        flight_num = ocr_flight.get('flight_number', '').strip()
        if flight_num:
            ocr_flight_map[flight_num] = ocr_flight
    
    merged_flights = []
    ocr_fields_used = set()  # 记录哪些字段来自OCR
    
    for llm_flight in llm_flights:
        flight_num = llm_flight.get('flight_number', '').strip()
        merged_flight = llm_flight.copy()
        field_sources = {}  # 记录每个字段的来源
        
        # 检查是否有对应的OCR结果
        ocr_flight = ocr_flight_map.get(flight_num)
        
        if ocr_flight:
            # 对于每个字段，如果大模型结果为空或无效，使用OCR结果
            fields_to_check = [
                'departure_airport', 'arrival_airport', 'flight_duration',
                'departure_terminal', 'arrival_terminal', 'aircraft_type',
                'price', 'discount_rate', 'cabin_class'
            ]
            
            for field in fields_to_check:
                llm_value = merged_flight.get(field, '').strip() if merged_flight.get(field) else ''
                ocr_value = ocr_flight.get(field, '').strip() if ocr_flight.get(field) else ''
                
                # 如果大模型字段为空或无效，使用OCR的值
                if not llm_value or llm_value in ['N/A', 'None', '']:
                    if ocr_value and ocr_value not in ['N/A', 'None', '']:
                        merged_flight[field] = ocr_value
                        field_sources[field] = 'ocr'
                        ocr_fields_used.add(field)
                else:
                    field_sources[field] = 'llm'
        
        # 标记字段来源（JSON格式）
        if field_sources:
            merged_flight['field_sources'] = json.dumps(field_sources)
        else:
            # 所有字段都来自大模型
            merged_flight['field_sources'] = json.dumps({})
        
        merged_flights.append(merged_flight)
    
    # 处理OCR中有但大模型中没有的航班
    llm_flight_numbers = {f.get('flight_number', '').strip() for f in llm_flights}
    for ocr_flight in ocr_flights:
        flight_num = ocr_flight.get('flight_number', '').strip()
        if flight_num and flight_num not in llm_flight_numbers:
            # 这个航班只被OCR识别到，标记所有字段来自OCR
            ocr_fields = {
                'airline', 'flight_number', 'departure_time', 'arrival_time',
                'departure_airport', 'arrival_airport', 'price', 'discount_rate',
                'cabin_class', 'aircraft_type', 'flight_duration',
                'has_stopover', 'stopover_city', 'is_shared_flight'
            }
            ocr_flight['field_sources'] = json.dumps(
                {field: 'ocr' for field in ocr_fields if ocr_flight.get(field)}
            )
            merged_flights.append(ocr_flight)
    
    return merged_flights


def get_ocr_fields(field_sources_json: str) -> Set[str]:
    """
    从field_sources JSON中提取来自OCR的字段
    
    Args:
        field_sources_json: field_sources字段的JSON字符串
    
    Returns:
        来自OCR的字段集合
    """
    if not field_sources_json:
        return set()
    
    try:
        sources = json.loads(field_sources_json)
        return {field for field, source in sources.items() if source == 'ocr'}
    except:
        return set()
