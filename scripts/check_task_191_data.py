#!/usr/bin/env python3
"""
检查任务191的数据是否正确保存
"""
import os
import sys

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 添加backend目录到路径（在Docker容器内，backend在/app下）
possible_paths = [
    os.path.join(os.path.dirname(script_dir), 'backend'),
    '/app',
    os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'backend'),
]

for path in possible_paths:
    if os.path.exists(path):
        sys.path.insert(0, path)
        break

try:
    try:
        from core.database import get_db
        from models.flight_result import FlightResult
        from models.task_record import TaskRecord
    except ImportError:
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
        from core.database import get_db
        from models.flight_result import FlightResult
        from models.task_record import TaskRecord
    
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    
    db: Session = next(get_db())
    
    print("=" * 80)
    print("检查任务191的数据")
    print("=" * 80)
    
    # 检查任务记录
    task = db.query(TaskRecord).filter(TaskRecord.id == 191).first()
    if task:
        print(f"\n✅ 任务191信息:")
        print(f"  任务ID: {task.id}")
        print(f"  任务名称: {task.task_name}")
        print(f"  状态: {task.status}")
        print(f"  航班数量: {task.flights_count}")
        print(f"  开始时间: {task.start_time}")
        print(f"  结束时间: {task.end_time}")
    else:
        print("\n❌ 任务191不存在")
        sys.exit(1)
    
    # 检查航班数据
    flights = db.query(FlightResult).filter(FlightResult.task_id == 191).all()
    print(f"\n📊 查询 task_id=191 的航班:")
    print(f"  找到 {len(flights)} 条航班记录")
    
    # 统计活跃航班
    active_flights = db.query(FlightResult).filter(
        FlightResult.task_id == 191,
        FlightResult.status == 'active'
    ).all()
    print(f"  活跃航班数量: {len(active_flights)} 条")
    
    # 统计非活跃航班
    inactive_flights = db.query(FlightResult).filter(
        FlightResult.task_id == 191,
        FlightResult.status != 'active'
    ).count()
    if inactive_flights > 0:
        print(f"  非活跃航班数量: {inactive_flights} 条")
    
    if flights:
        # 显示前10条记录的详细信息
        print(f"\n前10条记录详情:")
        for i, flight in enumerate(flights[:10], 1):
            print(f"  {i}. 航班号: {flight.flight_number}, "
                  f"出发: {flight.departure_city or flight.departure_airport} {flight.departure_time}, "
                  f"到达: {flight.arrival_city or flight.arrival_airport} {flight.arrival_time}, "
                  f"价格: {flight.price}, "
                  f"task_id: {flight.task_id}, "
                  f"状态: {flight.status}")
        
        # 统计唯一航班号
        unique_flight_numbers = set()
        for flight in flights:
            if flight.flight_number:
                unique_flight_numbers.add(flight.flight_number)
        print(f"\n📊 唯一航班号数量: {len(unique_flight_numbers)} 个")
        print(f"  航班号列表: {sorted(unique_flight_numbers)}")
        
        # 检查是否有重复记录
        flight_number_counts = {}
        for flight in flights:
            flight_num = flight.flight_number
            if flight_num:
                key = f"{flight_num}_{flight.departure_time}_{flight.arrival_time}_{flight.price}"
                flight_number_counts[key] = flight_number_counts.get(key, 0) + 1
        
        duplicates = {k: v for k, v in flight_number_counts.items() if v > 1}
        if duplicates:
            print(f"\n⚠️ 发现重复记录:")
            for key, count in duplicates.items():
                print(f"  {key}: {count} 条")
        else:
            print(f"\n✅ 未发现重复记录")
    else:
        print("\n❌ 未找到task_id=191的航班记录")
        
        # 检查是否有task_id为NULL的记录
        if task and task.start_time and task.end_time:
            from datetime import timedelta
            start_time = task.start_time - timedelta(minutes=10)
            end_time = task.end_time + timedelta(minutes=10)
            
            null_flights = db.query(FlightResult).filter(
                FlightResult.task_id.is_(None),
                FlightResult.status == 'active',
                FlightResult.scrape_time >= start_time,
                FlightResult.scrape_time <= end_time
            ).limit(30).all()
            
            if null_flights:
                print(f"\n⚠️ 找到 {len(null_flights)} 条task_id为NULL但时间匹配的航班记录（前30条）:")
                for i, flight in enumerate(null_flights, 1):
                    print(f"  {i}. 航班号: {flight.flight_number}, 抓取时间: {flight.scrape_time}")
    
    # 对比日志和数据库
    print(f"\n📊 对比分析:")
    print(f"  日志显示: 26 个唯一航班, 保存 26 条航班数据")
    print(f"  数据库记录: {len(flights)} 条总记录, {len(active_flights)} 条活跃记录")
    if flights and len(unique_flight_numbers) > 0:
        print(f"  唯一航班号: {len(unique_flight_numbers)} 个")
    
    if len(active_flights) == 26:
        print(f"\n✅ 数据库记录与日志一致！")
    elif len(active_flights) == 0:
        print(f"\n❌ 数据库中没有活跃记录，可能保存失败或task_id未正确设置")
    else:
        print(f"\n⚠️ 数据库记录数量 ({len(active_flights)}) 与日志不一致 (26)")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

