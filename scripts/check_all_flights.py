#!/usr/bin/env python3
"""
检查数据库中所有航班记录，查找可能保存失败的数据
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
    from sqlalchemy import func
    
    db: Session = next(get_db())
    
    print("=" * 80)
    print("检查数据库中所有航班记录")
    print("=" * 80)
    
    # 统计所有航班
    total_flights = db.query(FlightResult).count()
    active_flights = db.query(FlightResult).filter(FlightResult.status == 'active').count()
    
    print(f"\n📊 总体统计:")
    print(f"  总记录数: {total_flights}")
    print(f"  活跃记录数: {active_flights}")
    
    # 按task_id统计
    print(f"\n📊 按task_id统计:")
    task_id_stats = db.query(
        FlightResult.task_id,
        func.count(FlightResult.id).label('count')
    ).filter(
        FlightResult.status == 'active'
    ).group_by(FlightResult.task_id).all()
    
    for task_id, count in task_id_stats:
        if task_id is None:
            print(f"  task_id=NULL: {count} 条")
        else:
            print(f"  task_id={task_id}: {count} 条")
    
    # 检查任务191时间范围内的所有记录
    task = db.query(TaskRecord).filter(TaskRecord.id == 191).first()
    if task and task.start_time and task.end_time:
        start_time = task.start_time - timedelta(minutes=10)
        end_time = task.end_time + timedelta(minutes=10)
        
        time_range_flights = db.query(FlightResult).filter(
            FlightResult.status == 'active',
            FlightResult.scrape_time >= start_time,
            FlightResult.scrape_time <= end_time
        ).all()
        
        print(f"\n📊 任务191时间范围内的所有活跃航班记录:")
        print(f"  时间范围: {start_time} 到 {end_time}")
        print(f"  找到 {len(time_range_flights)} 条记录")
        
        if time_range_flights:
            # 按task_id分组统计
            task_id_groups = {}
            for flight in time_range_flights:
                task_id = flight.task_id if flight.task_id is not None else 'NULL'
                if task_id not in task_id_groups:
                    task_id_groups[task_id] = []
                task_id_groups[task_id].append(flight)
            
            print(f"\n按task_id分组:")
            for task_id, flights in task_id_groups.items():
                print(f"  task_id={task_id}: {len(flights)} 条")
                if task_id == 'NULL':
                    print(f"    前10条:")
                    for i, flight in enumerate(flights[:10], 1):
                        print(f"      {i}. {flight.flight_number}, 抓取时间: {flight.scrape_time}")
        else:
            print(f"\n⚠️ 未找到任何记录，可能数据根本没有保存到数据库")
    
    # 检查最近的记录
    recent_flights = db.query(FlightResult).filter(
        FlightResult.status == 'active'
    ).order_by(FlightResult.scrape_time.desc()).limit(30).all()
    
    print(f"\n📊 最近的30条活跃航班记录:")
    if recent_flights:
        for i, flight in enumerate(recent_flights, 1):
            print(f"  {i}. 航班号: {flight.flight_number}, "
                  f"task_id: {flight.task_id}, "
                  f"抓取时间: {flight.scrape_time}")
    else:
        print(f"  ⚠️ 没有活跃的航班记录")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()


