#!/usr/bin/env python3
"""
修复任务190的航班数据，如果task_id为NULL，根据scrape_time和任务时间匹配
"""
import os
import sys
from datetime import datetime, timedelta

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 添加backend目录到路径（在Docker容器内，backend在/app下）
# 尝试多种可能的路径
possible_paths = [
    os.path.join(os.path.dirname(script_dir), 'backend'),  # 本地开发
    '/app',  # Docker容器内
    os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'backend'),  # 另一种结构
]

for path in possible_paths:
    if os.path.exists(path):
        sys.path.insert(0, path)
        break

try:
    # 尝试从backend目录导入
    try:
        from core.database import get_db
        from models.flight_result import FlightResult
        from models.task_record import TaskRecord
    except ImportError:
        # 如果在Docker容器内，可能需要添加/app到路径
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
        from core.database import get_db
        from models.flight_result import FlightResult
        from models.task_record import TaskRecord
    
    from sqlalchemy.orm import Session
    
    db: Session = next(get_db())
    
    print("=" * 80)
    print("修复任务190的航班数据")
    print("=" * 80)
    
    # 获取任务190的信息
    task = db.query(TaskRecord).filter(TaskRecord.id == 190).first()
    if not task:
        print("\n❌ 任务190不存在")
        sys.exit(1)
    
    print(f"\n✅ 任务190信息:")
    print(f"  任务名称: {task.task_name}")
    print(f"  开始时间: {task.start_time}")
    print(f"  结束时间: {task.end_time}")
    
    # 查找task_id为NULL但时间在任务时间范围内的航班
    if task.start_time and task.end_time:
        # 扩展时间范围，前后各5分钟
        start_time = task.start_time - timedelta(minutes=5)
        end_time = task.end_time + timedelta(minutes=5)
        
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
                flight.task_id = 190
                print(f"  ✅ 修复航班 {flight.flight_number}: task_id = 190")
            
            db.commit()
            print(f"\n✅ 已修复 {len(null_flights)} 条航班记录的task_id")
        else:
            print("\n⚠️ 未找到需要修复的记录")
    else:
        print("\n⚠️ 任务190的开始时间或结束时间为空，无法匹配")
    
    # 重新统计航班数量
    flight_count = db.query(FlightResult).filter(
        FlightResult.task_id == 190,
        FlightResult.status == 'active'
    ).count()
    
    task.flights_count = flight_count
    db.commit()
    
    print(f"\n📊 任务190的航班数量已更新为: {flight_count}")
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()

