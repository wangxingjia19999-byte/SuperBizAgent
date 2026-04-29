"""
检索模块 - 根据查询检索相关文档
"""
from typing import List, Dict, Any
import logging
from app.core.config import get_logger, settings
from rag.embeddings import get_embedding_provider
from infrastructure.vector.chroma_store import get_vector_store

logger = get_logger(__name__)


class Retriever:
    """检索器"""
    
    def __init__(
        self,
        embedding_provider=None,
        vector_store=None,
        top_k: int = None,
        similarity_threshold: float = None
    ):
        """
        初始化检索器
        
        Args:
            embedding_provider: 向量提供者
            vector_store: 向量存储
            top_k: 返回的文档数量
            similarity_threshold: 相似度阈值
        """
        self.embedding_provider = embedding_provider or get_embedding_provider("local")
        self.vector_store = vector_store or get_vector_store()
        self.top_k = top_k or settings.RETRIEVER_TOP_K
        self.similarity_threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        根据查询字符串检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的文档数量
        
        Returns:
            检索结果列表
        """
        if top_k is None:
            top_k = self.top_k
        
        try:
            # 1. 将查询转换为向量
            query_embedding = self.embedding_provider.embed_text(query)
            
            # 2. 在向量库中搜索
            search_results = self.vector_store.search(query_embedding, top_k)
            
            # 3. 按相似度过滤
            filtered_results = [
                result for result in search_results
                if result["similarity"] >= self.similarity_threshold
            ]
            
            logger.info(
                f"Retrieved {len(filtered_results)} documents for query: {query[:50]}"
            )
            
            return filtered_results
        
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}': {str(e)}")
            return []
    
    def retrieve_with_metadata_filter(
        self,
        query: str,
        filter_key: str,
        filter_value: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        使用元数据过滤的检索
        
        Args:
            query: 查询文本
            filter_key: 元数据键
            filter_value: 元数据值
            top_k: 返回的文档数量
        
        Returns:
            检索结果列表
        """
        # 先检索所有结果
        all_results = self.retrieve(query, top_k or self.top_k * 3)
        
        # 进行元数据过滤
        filtered_results = [
            result for result in all_results
            if result.get("metadata", {}).get(filter_key) == filter_value
        ]
        
        # 返回 top_k 结果
        return filtered_results[:top_k or self.top_k]


class HybridRetriever:
    """混合检索器 - 结合向量检索和关键词检索"""
    
    def __init__(self, vector_retriever: Retriever = None):
        """
        初始化混合检索器
        
        Args:
            vector_retriever: 向量检索器
        """
        self.vector_retriever = vector_retriever or Retriever()
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回的文档数量
        
        Returns:
            检索结果列表
        """
        if top_k is None:
            top_k = self.vector_retriever.top_k
        
        try:
            # 1. 向量检索
            vector_results = self.vector_retriever.retrieve(query, top_k)
            
            # 2. 关键词检索（这里可以加入更复杂的逻辑）
            keyword_results = self._keyword_search(query, vector_results)
            
            # 3. 合并和去重
            merged_results = self._merge_results(vector_results, keyword_results)
            
            return merged_results[:top_k]
        
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {str(e)}")
            return self.vector_retriever.retrieve(query, top_k)
    
    def _keyword_search(self, query: str, existing_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """关键词搜索（简单实现）"""
        keywords = query.lower().split()
        
        enhanced_results = []
        for result in existing_results:
            content = result["content"].lower()
            keyword_matches = sum(1 for kw in keywords if kw in content)
            
            # 如果有多个关键词匹配，提升相似度
            if keyword_matches > 1:
                result["similarity"] += 0.1 * keyword_matches
            
            enhanced_results.append(result)
        
        return enhanced_results
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并检索结果"""
        # 使用向量检索的结果作为主要结果
        merged = {r["chunk_id"]: r for r in vector_results}
        
        # 根据 chunk_id 更新相似度
        for result in keyword_results:
            if result["chunk_id"] in merged:
                merged[result["chunk_id"]]["similarity"] = max(
                    merged[result["chunk_id"]]["similarity"],
                    result.get("similarity", 0)
                )
        
        # 按相似度排序
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x["similarity"],
            reverse=True
        )
        
        return sorted_results


def get_retriever(retriever_type: str = "vector") -> Retriever:
    """获取检索器"""
    if retriever_type == "vector":
        return Retriever()
    elif retriever_type == "hybrid":
        return HybridRetriever()
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")
