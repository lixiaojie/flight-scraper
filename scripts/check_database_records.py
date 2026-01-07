#!/usr/bin/env python3
"""
检查数据库中的航班记录
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
    print("检查数据库中的航班记录")
    print("=" * 80)
    
    # 检查任务190
    task = db.query(TaskRecord).filter(TaskRecord.id == 190).first()
    if task:
        print(f"\n✅ 任务190信息:")
        print(f"  任务ID: {task.id}")
        print(f"  任务名称: {task.task_name}")
        print(f"  状态: {task.status}")
        print(f"  航班数量: {task.flights_count}")
        print(f"  开始时间: {task.start_time}")
        print(f"  结束时间: {task.end_time}")
    else:
        print("\n❌ 任务190不存在")
    
    # 统计所有航班记录
    total_flights = db.query(FlightResult).count()
    active_flights = db.query(FlightResult).filter(FlightResult.status == 'active').count()
    print(f"\n📊 所有航班记录统计:")
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
    
    # 检查task_id=190的记录
    task_190_flights = db.query(FlightResult).filter(
        FlightResult.task_id == 190,
        FlightResult.status == 'active'
    ).all()
    print(f"\n📊 task_id=190的航班记录:")
    print(f"  找到 {len(task_190_flights)} 条记录")
    
    if task_190_flights:
        print(f"\n前10条记录:")
        for i, flight in enumerate(task_190_flights[:10], 1):
            print(f"  {i}. 航班号: {flight.flight_number}, task_id: {flight.task_id}, "
                  f"抓取时间: {flight.scrape_time}, 状态: {flight.status}")
    else:
        print("\n⚠️ 未找到task_id=190的记录")
        
        # 检查是否有task_id为NULL的记录
        null_flights = db.query(FlightResult).filter(
            FlightResult.task_id.is_(None),
            FlightResult.status == 'active'
        ).limit(20).all()
        print(f"\n⚠️ 找到 {len(null_flights)} 条task_id为NULL的活跃航班记录（前20条）:")
        for i, flight in enumerate(null_flights, 1):
            print(f"  {i}. 航班号: {flight.flight_number}, 抓取时间: {flight.scrape_time}")
    
    # 检查任务190时间范围内的所有记录
    if task and task.start_time and task.end_time:
        from datetime import timedelta
        start_time = task.start_time - timedelta(minutes=10)
        end_time = task.end_time + timedelta(minutes=10)
        
        time_range_flights = db.query(FlightResult).filter(
            FlightResult.status == 'active',
            FlightResult.scrape_time >= start_time,
            FlightResult.scrape_time <= end_time
        ).all()
        
        print(f"\n📊 任务190时间范围内的所有活跃航班记录:")
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
                if task_id == 'NULL' and len(flights) > 0:
                    print(f"    前5条:")
                    for i, flight in enumerate(flights[:5], 1):
                        print(f"      {i}. {flight.flight_number}, 抓取时间: {flight.scrape_time}")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()


