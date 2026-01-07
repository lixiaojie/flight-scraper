#!/usr/bin/env python3
"""
检查任务190的数据是否正确保存
"""
import os
import sys

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
    print("检查任务190的数据")
    print("=" * 80)
    
    # 检查任务记录
    task = db.query(TaskRecord).filter(TaskRecord.id == 190).first()
    if task:
        print(f"\n✅ 任务记录存在:")
        print(f"  任务ID: {task.id}")
        print(f"  任务名称: {task.task_name}")
        print(f"  状态: {task.status}")
        print(f"  航班数量: {task.flights_count}")
        print(f"  开始时间: {task.start_time}")
        print(f"  结束时间: {task.end_time}")
    else:
        print("\n❌ 任务记录不存在")
    
    # 检查航班数据
    flights = db.query(FlightResult).filter(FlightResult.task_id == 190).all()
    print(f"\n📊 查询 task_id=190 的航班:")
    print(f"  找到 {len(flights)} 条航班记录")
    
    if flights:
        # 检查前5条记录的task_id
        print(f"\n前5条记录的task_id:")
        for i, flight in enumerate(flights[:5], 1):
            print(f"  {i}. 航班号: {flight.flight_number}, task_id: {flight.task_id}, 状态: {flight.status}")
        
        # 统计task_id为NULL的记录
        null_task_id_count = db.query(FlightResult).filter(
            FlightResult.task_id.is_(None),
            FlightResult.status == 'active'
        ).count()
        print(f"\n⚠️ task_id为NULL的活跃航班数量: {null_task_id_count}")
        
        # 统计task_id=190的记录
        task_190_count = db.query(FlightResult).filter(
            FlightResult.task_id == 190,
            FlightResult.status == 'active'
        ).count()
        print(f"✅ task_id=190的活跃航班数量: {task_190_count}")
        
        # 检查是否有task_id不正确的记录
        incorrect_task_id = db.query(FlightResult).filter(
            FlightResult.task_id != 190,
            FlightResult.status == 'active',
            FlightResult.scrape_time >= task.start_time if task else None
        ).count()
        print(f"⚠️ 同一时间段内task_id不等于190的活跃航班数量: {incorrect_task_id}")
    else:
        print("\n❌ 未找到task_id=190的航班记录")
        
        # 检查是否有task_id为NULL的记录
        null_flights = db.query(FlightResult).filter(
            FlightResult.task_id.is_(None),
            FlightResult.status == 'active'
        ).limit(10).all()
        if null_flights:
            print(f"\n⚠️ 找到 {len(null_flights)} 条task_id为NULL的活跃航班记录（前10条）:")
            for i, flight in enumerate(null_flights, 1):
                print(f"  {i}. 航班号: {flight.flight_number}, 抓取时间: {flight.scrape_time}")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

