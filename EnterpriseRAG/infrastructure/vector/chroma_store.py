"""
向量存储模块 - 存储和检索向量
"""
from typing import List, Dict, Any, Optional
import logging
from app.core.config import get_logger, settings
from rag.embeddings import EmbeddingFactory

logger = get_logger(__name__)


class VectorStore:
    """向量存储基类"""
    
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """添加文档和向量"""
        raise NotImplementedError
    
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """搜索相似的文档"""
        raise NotImplementedError
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """删除文档"""
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """基于 Chroma 的向量存储"""
    
    def __init__(self, persist_dir: str = None):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            if persist_dir is None:
                persist_dir = str(settings.CHROMA_PERSIST_DIR)
            
            # 创建客户端
            self.client = chromadb.PersistentClient(path=persist_dir)
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name="enterprise_rag",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Initialized Chroma vector store at {persist_dir}")
        except ImportError:
            raise ImportError("Please install chromadb: pip install chromadb")
    
    def add_documents(
        self,
        document_ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> None:
        """添加文档到向量库"""
        try:
            self.collection.add(
                ids=document_ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Added {len(document_ids)} documents to Chroma")
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma: {str(e)}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """使用向量搜索相似文档"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # 转换结果格式
            search_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i, chunk_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # 转换距离为相似度
                    
                    search_results.append({
                        "chunk_id": chunk_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": float(similarity)
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search in Chroma: {str(e)}")
            raise
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """删除文档"""
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from Chroma")
        except Exception as e:
            logger.error(f"Failed to delete documents from Chroma: {str(e)}")
            raise
    
    def clear_collection(self) -> None:
        """清空所有数据（仅用于测试）"""
        try:
            # 获取所有 IDs
            all_data = self.collection.get()
            if all_data["ids"]:
                self.collection.delete(ids=all_data["ids"])
            logger.info("Cleared Chroma collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            raise


class VectorStoreFactory:
    """向量存储工厂"""
    
    _store = None
    
    @classmethod
    def get_store(cls, store_type: str = "chroma") -> VectorStore:
        """获取向量存储"""
        
        if cls._store is not None:
            return cls._store
        
        if store_type == "chroma":
            cls._store = ChromaVectorStore()
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
        
        return cls._store
    
    @classmethod
    def set_store(cls, store: VectorStore) -> None:
        """设置自定义向量存储"""
        cls._store = store


def get_vector_store(store_type: str = "chroma") -> VectorStore:
    """快捷方法获取向量存储"""
    return VectorStoreFactory.get_store(store_type)


def add_chunks_to_vector_store(
    chunks: List[Dict[str, Any]],
    vector_store: VectorStore = None
) -> None:
    """
    将 chunks 添加到向量库
    
    Args:
        chunks: 包含 embedding 的 chunk 列表
        vector_store: 向量存储实例
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    # 准备数据
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [
        {
            "document_id": chunk.get("document_id", ""),
            "file_name": chunk.get("file_name", ""),
            "section": chunk.get("section", ""),
            "page": chunk.get("page", 0)
        }
        for chunk in chunks
    ]
    embeddings = [chunk["embedding"] for chunk in chunks]
    
    # 添加到向量库
    vector_store.add_documents(chunk_ids, documents, metadatas, embeddings)
