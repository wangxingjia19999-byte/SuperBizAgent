"""
QA 链模块 - 整合问答流程
"""
from typing import List, Dict, Any, Optional
import logging
from app.core.config import get_logger, settings
from rag.retriever import Retriever, HybridRetriever
from rag.prompt_builder import PromptBuilder
from rag.embeddings import get_embedding_provider

logger = get_logger(__name__)


class LLMProvider:
    """大语言模型提供者"""
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """生成文本"""
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI LLM 提供者"""
    
    def __init__(self, model: str = "gpt-4", api_key: str = None):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """使用 OpenAI 生成文本"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise


class MockLLMProvider(LLMProvider):
    """模拟 LLM（用于测试）"""
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """模拟生成文本"""
        # 简单的模拟实现，提取参考资料中的内容
        if "参考资料：" in prompt:
            lines = prompt.split("参考资料：")[1].split("\n")
            relevant_content = []
            for line in lines[:3]:  # 取前三行
                if line.strip() and not line.startswith("【"):
                    relevant_content.append(line.strip())
            
            if relevant_content:
                return "\n".join(relevant_content) + "\n\n根据上述参考资料生成的回答。"
        
        return "根据当前知识库无法确定该问题的答案。"


class QAChain:
    """问答链 - 整合检索、Prompt 构造和 LLM 调用"""
    
    def __init__(
        self,
        retriever: Retriever = None,
        llm_provider: LLMProvider = None,
        prompt_builder: PromptBuilder = None,
        use_hybrid_retrieval: bool = False
    ):
        """
        初始化 QA 链
        
        Args:
            retriever: 检索器
            llm_provider: LLM 提供者
            prompt_builder: Prompt 构造器
            use_hybrid_retrieval: 是否使用混合检索
        """
        if use_hybrid_retrieval:
            self.retriever = HybridRetriever()
        else:
            self.retriever = retriever or Retriever()
        
        self.llm_provider = llm_provider or MockLLMProvider()
        self.prompt_builder = prompt_builder or PromptBuilder()
    
    def answer(
        self,
        query: str,
        top_k: int = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        回答问题
        
        Args:
            query: 问题
            top_k: 检索的文档数量
            temperature: LLM 温度参数
            max_tokens: LLM 最大 token 数
        
        Returns:
            回答结果
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS
        
        try:
            # 1. 检索相关文档
            retrieved_docs = self.retriever.retrieve(query, top_k)
            
            if not retrieved_docs:
                return {
                    "query": query,
                    "answer": self.prompt_builder.build_no_answer_response(query),
                    "citations": [],
                    "confidence": 0.0,
                    "retrieval_count": 0
                }
            
            # 2. 构造 Prompt
            prompt = self.prompt_builder.build_rag_prompt(query, retrieved_docs)
            
            # 3. 调用 LLM 生成答案
            answer = self.llm_provider.generate(prompt, temperature, max_tokens)
            
            # 4. 提取引用信息
            citations = self._extract_citations(retrieved_docs)
            
            # 5. 计算置信度（基于最高相似度）
            confidence = max(doc["similarity"] for doc in retrieved_docs) if retrieved_docs else 0
            
            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "confidence": float(confidence),
                "retrieval_count": len(retrieved_docs)
            }
        
        except Exception as e:
            logger.error(f"QA chain failed: {str(e)}")
            return {
                "query": query,
                "answer": f"抱歉，系统出现错误: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "retrieval_count": 0
            }
    
    def answer_with_history(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        top_k: int = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        基于对话历史回答问题
        
        Args:
            query: 当前问题
            conversation_history: 对话历史
            top_k: 检索的文档数量
            temperature: LLM 温度参数
            max_tokens: LLM 最大 token 数
        
        Returns:
            回答结果
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS
        
        try:
            # 1. 检索相关文档
            retrieved_docs = self.retriever.retrieve(query, top_k)
            
            if not retrieved_docs:
                return {
                    "query": query,
                    "answer": self.prompt_builder.build_no_answer_response(query),
                    "citations": [],
                    "confidence": 0.0,
                    "retrieval_count": 0
                }
            
            # 2. 构造多轮对话 Prompt
            prompt = self.prompt_builder.build_multi_turn_prompt(
                conversation_history,
                retrieved_docs
            )
            
            # 3. 调用 LLM 生成答案
            answer = self.llm_provider.generate(prompt, temperature, max_tokens)
            
            # 4. 提取引用信息
            citations = self._extract_citations(retrieved_docs)
            
            # 5. 计算置信度
            confidence = max(doc["similarity"] for doc in retrieved_docs) if retrieved_docs else 0
            
            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "confidence": float(confidence),
                "retrieval_count": len(retrieved_docs)
            }
        
        except Exception as e:
            logger.error(f"Multi-turn QA chain failed: {str(e)}")
            return {
                "query": query,
                "answer": f"抱歉，系统出现错误: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "retrieval_count": 0
            }
    
    def _extract_citations(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取引用信息"""
        citations = []
        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            citations.append({
                "document_name": metadata.get("file_name", "未知"),
                "section": metadata.get("section", ""),
                "similarity": doc.get("similarity", 0)
            })
        return citations


def get_qa_chain(
    use_mock: bool = False,
    use_hybrid_retrieval: bool = False
) -> QAChain:
    """获取 QA 链"""
    if use_mock:
        llm_provider = MockLLMProvider()
    else:
        try:
            llm_provider = OpenAIProvider(
                model=settings.LLM_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
        except:
            logger.warning("OpenAI not available, using mock LLM")
            llm_provider = MockLLMProvider()
    
    return QAChain(
        llm_provider=llm_provider,
        use_hybrid_retrieval=use_hybrid_retrieval
    )
