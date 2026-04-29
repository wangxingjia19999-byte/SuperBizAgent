import logging
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置"""
    
    # 基础配置
    APP_NAME: str = "EnterpriseRAG"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # FastAPI
    API_V1_STR: str = "/api/v1"
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = Path("logs")
    
    # 文件存储
    UPLOAD_DIR: Path = Path("data/uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # 向量数据库 (Chroma)
    VECTOR_DB_TYPE: str = "chroma"  # chroma, milvus, pgvector
    CHROMA_PERSIST_DIR: Path = Path("data/chroma")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # 本地 Embedding 模型，或使用 openai
    
    # LLM 配置
    LLM_MODEL: str = "gpt-4"  # 或使用其他模型
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1000
    
    # OpenAI API (如果使用)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    
    # 数据库 (暂时不使用，后续第二阶段)
    DATABASE_URL: str = "sqlite:///./enterprise_rag.db"
    
    # Redis (可选)
    REDIS_URL: Optional[str] = None
    
    # 文本切分参数
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # 检索参数
    RETRIEVER_TOP_K: int = 3
    RERANKER_TOP_K: int = 3
    SIMILARITY_THRESHOLD: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def init_directories() -> None:
    """初始化必要的目录"""
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    logger = logging.getLogger(name)
    
    # 设置日志级别
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 如果已有处理器，则直接返回
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = settings.LOG_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
