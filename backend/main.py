"""
FastAPI主应用
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from backend.core.database import get_db
    from backend.models.flight_result import FlightResult
    from backend.schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
    from backend.api.endpoints.task_endpoints import router as task_router
    from backend.api.endpoints.admin_endpoints import router as admin_router
    from backend.api.endpoints.system_endpoints import router as system_router
    HAS_ROUTERS = True
except ImportError:
    # Docker容器中的简化导入
    from core.database import get_db
    from models.flight_result import FlightResult
    from schemas.flight_schema import FlightResultResponse, FlightStatisticsResponse
    HAS_ROUTERS = False

# 创建FastAPI应用
app = FastAPI(
    title="航班信息API",
    description="12306航班信息抓取和查询API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（仅在本地环境）
if HAS_ROUTERS:
    app.include_router(task_router)
    app.include_router(admin_router)
    app.include_router(system_router)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "航班信息API服务正在运行", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务正常运行"}

@app.get("/api/flights", response_model=List[FlightResultResponse])
async def get_flights(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    airline: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取航班列表"""
    try:
        query = db.query(FlightResult).filter(FlightResult.status == 'active')
        
        if min_price is not None:
            query = query.filter(FlightResult.price >= min_price)
        if max_price is not None:
            query = query.filter(FlightResult.price <= max_price)
        if airline:
            query = query.filter(FlightResult.airline.like(f'%{airline}%'))
        
        flights = query.order_by(FlightResult.price.asc()).limit(limit).all()
        
        return [flight.to_dict() for flight in flights]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flights/statistics", response_model=FlightStatisticsResponse)
async def get_flight_statistics(db: Session = Depends(get_db)):
    """获取航班统计信息"""
    try:
        total_flights = db.query(FlightResult).filter(FlightResult.status == 'active').count()
        
        if total_flights == 0:
            return {
                "total_flights": 0,
                "min_price": 0,
                "max_price": 0,
                "avg_price": 0
            }
        
        min_price = db.query(FlightResult).filter(
            FlightResult.status == 'active'
        ).order_by(FlightResult.price.asc()).first()
        
        max_price = db.query(FlightResult).filter(
            FlightResult.status == 'active'
        ).order_by(FlightResult.price.desc()).first()
        
        # 计算平均价格
        from sqlalchemy import func
        avg_result = db.query(func.avg(FlightResult.price)).filter(
            FlightResult.status == 'active'
        ).scalar()
        
        return {
            "total_flights": total_flights,
            "min_price": min_price.price if min_price else 0,
            "max_price": max_price.price if max_price else 0,
            "avg_price": round(avg_result or 0, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flights/batch-save")
async def batch_save_flights(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量保存航班数据"""
    try:
        flights = request.get('flights', [])
        source = request.get('source', '12306')
        saved_count = 0
        
        for flight_data in flights:
            flight_result = FlightResult(
                airline=flight_data.get('airline', ''),
                flight_number=flight_data.get('flight_number', ''),
                departure_time=flight_data.get('departure_time', ''),
                departure_airport=flight_data.get('departure_airport', ''),
                arrival_time=flight_data.get('arrival_time', ''),
                arrival_airport=flight_data.get('arrival_airport', ''),
                price=float(flight_data.get('price', 0)) if flight_data.get('price') else 0.0,
                currency=flight_data.get('currency', 'CNY'),
                source=source,
                raw_data=str(flight_data),
                notes=flight_data.get('notes', '')
            )
            
            db.add(flight_result)
            saved_count += 1
        
        db.commit()
        
        return {
            "message": f"成功保存 {saved_count} 条航班数据",
            "saved_count": saved_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
