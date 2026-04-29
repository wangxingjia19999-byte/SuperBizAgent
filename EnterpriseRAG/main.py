"""
FastAPI 应用主入口
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings, init_directories, get_logger
from app.api.v1.router import router as api_v1_router

# 初始化日志
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_directories()
    yield
    # 关闭
    logger.info(f"Stopping {settings.APP_NAME}")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="基于 RAG 的企业内部知识库问答系统",
        version=settings.APP_VERSION,
        lifespan=lifespan
    )
    
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 包含 API 路由
    app.include_router(api_v1_router)
    
    # 根路由
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api": "/api/v1"
        }
    
    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    logger.info("FastAPI application created successfully")
    
    return app


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
