#!/usr/bin/env python3
"""
根据航班号修复任务191的数据
从日志中提取的26个航班号，查找并更新task_id
"""
import os
import sys
from datetime import datetime, timedelta

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 添加backend目录到路径
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
    
    db: Session = next(get_db())
    
    print("=" * 80)
    print("根据航班号修复任务191的数据")
    print("=" * 80)
    
    # 从日志中提取的26个航班号
    task_191_flight_numbers = [
        'CA8538', 'FM9452', 'MU5819', 'MU5324', 'MU5811', 'MU8504',
        'CZ3678', 'MU5801', 'MU5803', 'MU5805', 'RH737', 'FM9454',
        'MU5821', 'MU8500', 'RH738', 'MU5817', 'MU8488', 'FM9430',
        'MU5813', 'MU5282', 'MU5438', 'MU5506', 'MU5815', 'MU5807',
        'MU5809', 'MU9709'
    ]
    
    print(f"\n📋 任务191的航班号列表（26个）:")
    for i, fn in enumerate(task_191_flight_numbers, 1):
        print(f"  {i}. {fn}")
    
    # 获取任务191的信息
    task = db.query(TaskRecord).filter(TaskRecord.id == 191).first()
    if not task:
        print("\n❌ 任务191不存在")
        sys.exit(1)
    
    print(f"\n✅ 任务191信息:")
    print(f"  任务名称: {task.task_name}")
    print(f"  开始时间: {task.start_time}")
    print(f"  结束时间: {task.end_time}")
    
    # 查找这些航班号且task_id为NULL的记录
    # 时间范围：任务开始时间前10分钟到结束时间后10分钟
    if task.start_time and task.end_time:
        start_time = task.start_time - timedelta(minutes=10)
        end_time = task.end_time + timedelta(minutes=10)
        
        # 查找匹配的航班
        matched_flights = db.query(FlightResult).filter(
            FlightResult.flight_number.in_(task_191_flight_numbers),
            FlightResult.task_id.is_(None),
            FlightResult.status == 'active',
            FlightResult.scrape_time >= start_time - timedelta(hours=8),  # 考虑时区差异
            FlightResult.scrape_time <= end_time + timedelta(hours=8)
        ).all()
        
        print(f"\n📊 找到 {len(matched_flights)} 条匹配的航班记录")
        
        if matched_flights:
            print("\n修复这些记录的task_id...")
            for flight in matched_flights:
                flight.task_id = 191
                print(f"  ✅ 修复航班 {flight.flight_number}: task_id = 191, 抓取时间: {flight.scrape_time}")
            
            db.commit()
            print(f"\n✅ 已修复 {len(matched_flights)} 条航班记录的task_id")
        else:
            # 如果时间范围匹配失败，尝试只根据航班号匹配
            print("\n⚠️ 时间范围匹配失败，尝试只根据航班号匹配...")
            matched_flights = db.query(FlightResult).filter(
                FlightResult.flight_number.in_(task_191_flight_numbers),
                FlightResult.task_id.is_(None),
                FlightResult.status == 'active'
            ).order_by(FlightResult.scrape_time.desc()).limit(30).all()
            
            if matched_flights:
                print(f"\n📊 找到 {len(matched_flights)} 条匹配的航班记录（仅根据航班号）")
                print("\n修复这些记录的task_id...")
                for flight in matched_flights:
                    flight.task_id = 191
                    print(f"  ✅ 修复航班 {flight.flight_number}: task_id = 191, 抓取时间: {flight.scrape_time}")
                
                db.commit()
                print(f"\n✅ 已修复 {len(matched_flights)} 条航班记录的task_id")
            else:
                print("\n⚠️ 未找到需要修复的记录")
    else:
        print("\n⚠️ 任务191的开始时间或结束时间为空，无法匹配")
    
    # 重新统计航班数量
    flight_count = db.query(FlightResult).filter(
        FlightResult.task_id == 191,
        FlightResult.status == 'active'
    ).count()
    
    task.flights_count = flight_count
    db.commit()
    
    print(f"\n📊 任务191的航班数量已更新为: {flight_count}")
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()


