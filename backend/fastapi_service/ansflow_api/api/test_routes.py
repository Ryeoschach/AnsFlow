"""
超简化的高性能API测试版本
"""
from fastapi import APIRouter
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """测试端点"""
    return {
        "message": "AnsFlow FastAPI 优化测试成功！",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "working"
    }

@router.get("/pipelines/simple")
async def get_pipelines_simple():
    """简单的Pipeline状态测试"""
    # 模拟数据库查询延迟
    await asyncio.sleep(0.1)
    
    return {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "主分支构建",
                "status": "running",
                "success_rate": 0.95
            },
            {
                "id": 2,
                "name": "测试部署",
                "status": "completed", 
                "success_rate": 0.88
            }
        ],
        "count": 2,
        "query_time": "100ms",
        "cached": False
    }

@router.get("/metrics/simple")
async def get_metrics_simple():
    """简单的系统指标"""
    await asyncio.sleep(0.05)
    
    import random
    return {
        "success": True,
        "data": {
            "active_pipelines": random.randint(5, 15),
            "success_rate": round(random.uniform(0.85, 0.98), 3),
            "avg_response_time": random.randint(50, 150),
            "health": "good"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
