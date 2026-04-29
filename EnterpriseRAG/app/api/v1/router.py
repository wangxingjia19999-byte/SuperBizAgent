"""
API v1 路由入口
"""
from fastapi import APIRouter
from app.api.v1 import routes_qa, routes_documents

router = APIRouter(prefix="/api/v1")

# 包含子路由
router.include_router(routes_qa.router)
router.include_router(routes_documents.router)


@router.get("")
async def api_root():
    """API 根路由"""
    return {
        "message": "Enterprise RAG API v1",
        "endpoints": {
            "qa": "/api/v1/qa",
            "documents": "/api/v1/documents"
        }
    }
