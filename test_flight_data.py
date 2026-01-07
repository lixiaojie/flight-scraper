#!/usr/bin/env python3
"""
测试脚本：创建包含新字段的航班数据
"""

import requests
import json


def create_test_flight_data():
    """创建测试航班数据"""

    # 测试航班数据
    test_flights = [
        {
            "airline": "中国南方航空",
            "flight_number": "CZ3568",
            "departure_date": "2025-10-08",
            "departure_time": "06:30",
            "departure_airport": "乌鲁木齐地窝堡国际机场",
            "arrival_time": "08:50",
            "arrival_airport": "北京首都国际机场",
            "flight_duration": "2h20m",
            "price": 500.0,
            "currency": "CNY",
            "source": "12306",
            "status": "active"
        },
        {
            "airline": "中国国际航空",
            "flight_number": "CA1234",
            "departure_date": "2025-10-08",
            "departure_time": "09:15",
            "departure_airport": "乌鲁木齐地窝堡国际机场",
            "arrival_time": "11:35",
            "arrival_airport": "北京首都国际机场",
            "flight_duration": "2h20m",
            "price": 650.0,
            "currency": "CNY",
            "source": "12306",
            "status": "active"
        },
        {
            "airline": "中国东方航空",
            "flight_number": "MU5678",
            "departure_date": "2025-10-08",
            "departure_time": "14:20",
            "departure_airport": "乌鲁木齐地窝堡国际机场",
            "arrival_time": "16:40",
            "arrival_airport": "北京首都国际机场",
            "flight_duration": "2h20m",
            "price": 580.0,
            "currency": "CNY",
            "source": "12306",
            "status": "active"
        }
    ]

    # 发送到后端API
    api_url = "http://localhost:8000/api/flights/batch-save"
    payload = {
        "flights": test_flights,
        "source": "12306"
    }

    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            print("✅ 测试航班数据创建成功")
            result = response.json()
            print(f"保存了 {result.get('message', '')}")
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 请求失败: {e}")


if __name__ == "__main__":
    create_test_flight_data()
