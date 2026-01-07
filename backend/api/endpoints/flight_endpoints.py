"""
航班API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from core.database import get_db
from services.flight_service import FlightService
from models.flight_result import FlightResult
from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/", response_model=List[FlightResultResponse])
async def get_flights(
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    airline: Optional[str] = Query(None, description="航空公司"),
    flight_number: Optional[str] = Query(None, description="航班号"),
    departure_city: Optional[str] = Query(None, description="出发城市"),
    arrival_city: Optional[str] = Query(None, description="到达城市"),
    task_id: Optional[int] = Query(None, description="任务编号"),
    sort_by: str = Query("price", description="排序方式: price(价格) 或 time(时间)"),
    limit: int = Query(50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取航班列表，按任务分组并按指定方式排序"""
    try:
        flight_service = FlightService(db)

        # 强制使用任务分组查询，并应用筛选条件
        print(
            f"🔍 强制使用任务分组查询: limit={limit}, sort_by={sort_by}, flight_number={flight_number}, departure_city={departure_city}, arrival_city={arrival_city}, task_id={task_id} (type: {type(task_id).__name__})")
        
        # 如果指定了 task_id，确保它是有效的整数
        if task_id is not None:
            print(f"🔍 接收到 task_id: {task_id} (type: {type(task_id).__name__})")
            if not isinstance(task_id, int) or task_id <= 0:
                print(f"⚠️ 无效的 task_id: {task_id}，返回空列表")
                return []
            print(f"✅ task_id 验证通过: {task_id}")
        else:
            print("ℹ️ 未指定 task_id，将查询所有活跃的航班（包括有 task_id 和没有 task_id 的）")
        
        flights = flight_service.get_flights_grouped_by_task(
            limit=limit,
            sort_by=sort_by,
            flight_number=flight_number,
            departure_city=departure_city,
            arrival_city=arrival_city,
            task_id=task_id
        )

        # 如果指定了 task_id 但没有结果，返回空列表
        if task_id is not None and len(flights) == 0:
            print(f"⚠️ 任务编号 {task_id} 无命中结果，返回空列表")
        elif task_id is not None:
            print(f"✅ 任务编号 {task_id} 找到 {len(flights)} 条航班记录")
        else:
            print(f"✅ 查询所有有 task_id 的航班，找到 {len(flights)} 条记录")
        
        return [flight.to_dict() for flight in flights]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=FlightStatisticsResponse)
async def get_flight_statistics(db: Session = Depends(get_db)):
    """获取航班统计信息"""
    try:
        flight_service = FlightService(db)
        stats = flight_service.get_flight_statistics()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-date")
async def get_flights_by_date(
    date: str = Query(..., description="日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """根据日期查询航班"""
    try:
        flight_service = FlightService(db)
        target_date = datetime.strptime(date, "%Y-%m-%d")
        flights = flight_service.get_flights_by_date(target_date)

        return [flight.to_dict() for flight in flights]

    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-time-range")
async def get_flights_by_time_range(
    start_time: str = Query(..., description="开始时间 (HH:MM)"),
    end_time: str = Query(..., description="结束时间 (HH:MM)"),
    db: Session = Depends(get_db)
):
    """根据时间范围查询航班"""
    try:
        flight_service = FlightService(db)
        flights = flight_service.get_flights_by_time_range(
            start_time, end_time)

        return [flight.to_dict() for flight in flights]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_flights(
    days: int = Query(7, description="保留天数"),
    db: Session = Depends(get_db)
):
    """清理旧航班数据"""
    try:
        flight_service = FlightService(db)
        deleted_count = flight_service.delete_old_flights(days)

        return {"message": f"成功删除 {deleted_count} 条旧航班数据"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-save")
async def batch_save_flights(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量保存航班数据"""
    try:
        flights = request.get("flights", [])
        source = request.get("source", "12306")
        task_id = request.get("task_id")

        # 确保 task_id 是整数类型
        if task_id is not None:
            try:
                task_id = int(task_id)
            except (ValueError, TypeError):
                print(f"⚠️ task_id 格式错误: {task_id}，将设置为 None")
                task_id = None

        print(
            f"🔍 接收到的参数: flights={len(flights)}, source={source}, task_id={task_id} (type: {type(task_id).__name__})")

        # 如果提供了task_id，获取任务的结束时间作为scrape_time
        # 如果任务还没有结束时间，先设置结束时间
        scrape_time = None
        if task_id:
            try:
                from models.task_record import TaskRecord
                import pytz
                task = db.query(TaskRecord).filter(
                    TaskRecord.id == task_id).first()
                if task:
                    if task.end_time:
                        scrape_time = task.end_time
                        print(f"📅 使用任务 {task_id} 的结束时间作为抓取时间: {scrape_time}")
                    else:
                        # 如果任务还没有结束时间，先设置结束时间
                        shanghai_tz = pytz.timezone('Asia/Shanghai')
                        scrape_time = datetime.now(
                            shanghai_tz).replace(tzinfo=None)
                        task.end_time = scrape_time
                        db.commit()
                        print(f"📅 任务 {task_id} 还没有结束时间，设置为当前时间: {scrape_time}")
            except Exception as e:
                print(f"⚠️ 获取任务结束时间失败: {e}")
                import traceback
                traceback.print_exc()

        flight_service = FlightService(db)
        saved_flights = flight_service.save_flight_results(
            flights, source, task_id, scrape_time)

        print(
            f"🔍 保存结果: saved_flights数量={len(saved_flights) if saved_flights else 0}, task_id={task_id}, task_id类型={type(task_id).__name__}")

        # 保存航班后，更新任务的航班数量
        if task_id:
            try:
                from models.task_record import TaskRecord
                task = db.query(TaskRecord).filter(
                    TaskRecord.id == task_id).first()
                if task:
                    # 重新统计航班数量（无论saved_flights是否为空，都要统计）
                    from models.flight_result import FlightResult
                    flight_count = db.query(FlightResult).filter(
                        FlightResult.task_id == task_id,
                        FlightResult.status == 'active'
                    ).count()
                    print(
                        f"🔍 数据库查询结果: task_id={task_id}, 查询到的航班数量={flight_count}, 本次保存了 {len(saved_flights) if saved_flights else 0} 条航班")
                    task.flights_count = flight_count
                    db.commit()
                    print(
                        f"📊 任务 {task_id} 航班数量已更新为: {flight_count}")

                    # 再次验证更新后的值
                    db.refresh(task)
                    print(
                        f"🔍 验证: 任务 {task_id} 的 flights_count 字段值={task.flights_count}")
                    
                    # 验证保存的航班是否有正确的task_id
                    if saved_flights:
                        sample_flight = saved_flights[0]
                        print(
                            f"🔍 验证: 保存的航班示例 task_id={sample_flight.task_id if hasattr(sample_flight, 'task_id') else 'N/A'}")
                else:
                    print(f"⚠️ 任务 {task_id} 未找到，无法更新航班数量")
            except Exception as e:
                print(f"⚠️ 更新任务航班数量失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ task_id 为空，跳过更新航班数量")

        return {
            "message": f"成功保存 {len(saved_flights)} 条航班数据",
            "saved_count": len(saved_flights)
        }

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
