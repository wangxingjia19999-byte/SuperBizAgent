"""
向量化模块 - 生成文本的 Embedding 向量
"""
from typing import List, Union
import logging
import numpy as np
from app.core.config import get_logger, settings

logger = get_logger(__name__)


class EmbeddingProvider:
    """向量提供者基类"""
    
    def embed_text(self, text: str) -> List[float]:
        """生成单个文本的向量"""
        raise NotImplementedError
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        raise NotImplementedError
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        raise NotImplementedError


class OpenAIEmbedding(EmbeddingProvider):
    """使用 OpenAI 的 Embedding"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: str = None):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
            self._dimension = None
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def embed_text(self, text: str) -> List[float]:
        """使用 OpenAI 生成向量"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            # 按输入顺序排序
            embeddings = [None] * len(texts)
            for data in response.data:
                embeddings[data.index] = data.embedding
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        if self._dimension is None:
            # 测试一个小文本来获取维度
            embedding = self.embed_text("test")
            self._dimension = len(embedding)
        return self._dimension


class LocalEmbedding(EmbeddingProvider):
    """使用本地模型生成 Embedding"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded local embedding model: {model_name}")
        except ImportError:
            raise ImportError(
                "Please install sentence-transformers: "
                "pip install sentence-transformers"
            )
    
    def embed_text(self, text: str) -> List[float]:
        """生成单个文本向量"""
        return self.model.encode(text, convert_to_numpy=False).tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        embeddings = self.model.encode(texts, convert_to_numpy=False)
        return [emb.tolist() for emb in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        embedding = self.embed_text("test")
        return len(embedding)


class ChromaDefaultEmbedding(EmbeddingProvider):
    """使用 Chroma 的默认 Embedding"""
    
    def __init__(self):
        try:
            from chromadb.utils import embedding_functions
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            logger.info("Using Chroma default embedding")
        except ImportError:
            raise ImportError("Please install chromadb: pip install chromadb")
    
    def embed_text(self, text: str) -> List[float]:
        """生成单个文本向量"""
        embeddings = self.embedding_function([text])
        return embeddings[0].tolist() if embeddings else []
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        embeddings = self.embedding_function(texts)
        return [emb.tolist() for emb in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        embedding = self.embed_text("test")
        return len(embedding)


class EmbeddingFactory:
    """向量提供者工厂"""
    
    _provider = None
    
    @classmethod
    def get_provider(cls, provider_type: str = "local") -> EmbeddingProvider:
        """获取向量提供者"""
        
        if cls._provider is not None:
            return cls._provider
        
        if provider_type == "openai":
            cls._provider = OpenAIEmbedding(api_key=settings.OPENAI_API_KEY)
        elif provider_type == "local":
            cls._provider = LocalEmbedding()
        elif provider_type == "chroma":
            cls._provider = ChromaDefaultEmbedding()
        else:
            raise ValueError(f"Unknown embedding provider: {provider_type}")
        
        logger.info(f"Initialized embedding provider: {provider_type}")
        return cls._provider
    
    @classmethod
    def set_provider(cls, provider: EmbeddingProvider) -> None:
        """设置自定义向量提供者"""
        cls._provider = provider


def get_embedding_provider(provider_type: str = "local") -> EmbeddingProvider:
    """快捷方法获取 embedding 提供者"""
    return EmbeddingFactory.get_provider(provider_type)


def embed_chunks(chunks: List[dict], provider: EmbeddingProvider = None) -> List[dict]:
    """
    为 chunks 生成 embeddings
    
    Args:
        chunks: chunk 列表 (来自 TextSplitter)
        provider: embedding 提供者
    
    Returns:
        带有 embedding 的 chunk 列表
    """
    if provider is None:
        provider = get_embedding_provider("local")
    
    # 提取所有 chunk 的内容
    contents = [chunk["content"] for chunk in chunks]
    
    # 批量生成 embeddings
    embeddings = provider.embed_documents(contents)
    
    # 将 embeddings 添加到 chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    logger.info(f"Generated embeddings for {len(chunks)} chunks")
    
    return chunks
