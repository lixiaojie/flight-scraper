#!/usr/bin/env python3
"""
修复任务191的航班数据，如果task_id为NULL，根据scrape_time和任务时间匹配
"""
import os
import sys
from datetime import datetime, timedelta

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
    
    db: Session = next(get_db())
    
    print("=" * 80)
    print("修复任务191的航班数据")
    print("=" * 80)
    
    # 获取任务191的信息
    task = db.query(TaskRecord).filter(TaskRecord.id == 191).first()
    if not task:
        print("\n❌ 任务191不存在")
        sys.exit(1)
    
    print(f"\n✅ 任务191信息:")
    print(f"  任务名称: {task.task_name}")
    print(f"  开始时间: {task.start_time}")
    print(f"  结束时间: {task.end_time}")
    
    # 查找task_id为NULL但时间在任务时间范围内的航班
    if task.start_time and task.end_time:
        # 扩展时间范围，前后各10分钟
        start_time = task.start_time - timedelta(minutes=10)
        end_time = task.end_time + timedelta(minutes=10)
        
        null_flights = db.query(FlightResult).filter(
            FlightResult.task_id.is_(None),
            FlightResult.status == 'active',
            FlightResult.scrape_time >= start_time,
            FlightResult.scrape_time <= end_time
        ).all()
        
        print(f"\n📊 找到 {len(null_flights)} 条task_id为NULL但时间匹配的航班记录")
        
        if null_flights:
            print("\n修复这些记录的task_id...")
            for flight in null_flights:
                flight.task_id = 191
                print(f"  ✅ 修复航班 {flight.flight_number}: task_id = 191")
            
            db.commit()
            print(f"\n✅ 已修复 {len(null_flights)} 条航班记录的task_id")
        else:
            print("\n⚠️ 未找到需要修复的记录")
            
            # 检查是否有其他task_id的记录
            other_flights = db.query(FlightResult).filter(
                FlightResult.status == 'active',
                FlightResult.scrape_time >= start_time,
                FlightResult.scrape_time <= end_time
            ).all()
            
            if other_flights:
                print(f"\n📊 找到 {len(other_flights)} 条时间匹配的航班记录:")
                task_id_groups = {}
                for flight in other_flights:
                    task_id = flight.task_id if flight.task_id is not None else 'NULL'
                    if task_id not in task_id_groups:
                        task_id_groups[task_id] = []
                    task_id_groups[task_id].append(flight)
                
                for task_id, flights in task_id_groups.items():
                    print(f"  task_id={task_id}: {len(flights)} 条")
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


