#!/usr/bin/env python3
"""
查询指定任务的航班记录
"""
import os
import sys
import json
from pathlib import Path

# 添加backend目录到路径
# 尝试多种路径
possible_paths = [
    Path(__file__).parent.parent / 'backend',  # 本地路径
    Path('/app/backend'),  # Docker容器路径
    Path('/app'),  # Docker容器根路径
]

backend_path = None
for path in possible_paths:
    if path.exists():
        backend_path = path
        sys.path.insert(0, str(path))
        break

if not backend_path:
    # 如果都不存在，尝试直接导入（可能在Docker容器中已配置好路径）
    pass

try:
    from core.database import get_db
    from models.flight_result import FlightResult
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n💡 提示:")
    print("   如果在Docker容器中运行:")
    print("   docker-compose exec web python3 /app/scripts/query_task_flights.py 209")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def query_task_flights(task_id: int):
    """查询指定任务的航班记录"""
    print("=" * 80)
    print(f"查询任务 {task_id} 的航班记录")
    print("=" * 80)
    
    try:
        db = next(get_db())
        
        # 查询该任务的所有航班
        flights = db.query(FlightResult).filter(
            FlightResult.task_id == task_id,
            FlightResult.status == 'active'
        ).order_by(FlightResult.price).all()
        
        if not flights:
            print(f"\n⚠️ 未找到任务 {task_id} 的航班记录")
            return
        
        print(f"\n✅ 找到 {len(flights)} 条航班记录\n")
        
        # 打印每条记录的详细信息
        for i, flight in enumerate(flights, 1):
            print("=" * 80)
            print(f"航班 {i}/{len(flights)}")
            print("=" * 80)
            
            # 转换为字典并打印
            flight_dict = flight.to_dict()
            
            print(f"ID: {flight_dict.get('id')}")
            print(f"任务ID: {flight_dict.get('task_id')}")
            print(f"航空公司: {flight_dict.get('airline')}")
            print(f"航班号: {flight_dict.get('flight_number')}")
            print(f"是否共享航班: {flight_dict.get('is_shared_flight', '否')}")
            print(f"机型: {flight_dict.get('aircraft_type', 'N/A')}")
            print(f"出发日期: {flight_dict.get('departure_date', 'N/A')}")
            print(f"出发时间: {flight_dict.get('departure_time')}")
            print(f"到达时间: {flight_dict.get('arrival_time')}")
            print(f"出发机场: {flight_dict.get('departure_airport', 'N/A')} ({flight_dict.get('departure_airport_name', 'N/A')})")
            print(f"到达机场: {flight_dict.get('arrival_airport', 'N/A')} ({flight_dict.get('arrival_airport_name', 'N/A')})")
            print(f"出发城市: {flight_dict.get('departure_city', 'N/A')}")
            print(f"到达城市: {flight_dict.get('arrival_city', 'N/A')}")
            print(f"出发航站楼: {flight_dict.get('departure_terminal', 'N/A')}")
            print(f"到达航站楼: {flight_dict.get('arrival_terminal', 'N/A')}")
            print(f"飞行时长: {flight_dict.get('flight_duration', 'N/A')}")
            print(f"是否经停: {flight_dict.get('has_stopover', '否')}")
            if flight_dict.get('has_stopover') == '是':
                print(f"经停城市: {flight_dict.get('stopover_city', 'N/A')}")
                print(f"经停机场: {flight_dict.get('stopover_airport', 'N/A')}")
            print(f"价格: ¥{flight_dict.get('price', 0.0)}")
            print(f"货币: {flight_dict.get('currency', 'CNY')}")
            print(f"舱位等级: {flight_dict.get('cabin_class', 'N/A')}")
            print(f"折扣率: {flight_dict.get('discount_rate', 'N/A')}")
            print(f"原价: {flight_dict.get('original_price', 'N/A')}")
            print(f"数据源: {flight_dict.get('source', 'N/A')}")
            print(f"状态: {flight_dict.get('status', 'N/A')}")
            print(f"抓取时间: {flight_dict.get('scrape_time', 'N/A')}")
            if flight_dict.get('notes'):
                print(f"备注: {flight_dict.get('notes')}")
            
            print()
        
        # 打印JSON格式（便于复制）
        print("=" * 80)
        print("JSON格式数据:")
        print("=" * 80)
        flights_json = [flight.to_dict() for flight in flights]
        print(json.dumps(flights_json, ensure_ascii=False, indent=2))
        
        print("\n" + "=" * 80)
        print("✅ 查询完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 query_task_flights.py <task_id>")
        print("示例: python3 query_task_flights.py 209")
        sys.exit(1)
    
    try:
        task_id = int(sys.argv[1])
        query_task_flights(task_id)
    except ValueError:
        print(f"❌ 无效的任务ID: {sys.argv[1]}")
        sys.exit(1)
