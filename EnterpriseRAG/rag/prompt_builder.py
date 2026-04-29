"""
Prompt 构造模块 - 为大模型构造输入 Prompt
"""
from typing import List, Dict, Any
import logging
from app.core.config import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Prompt 构造器"""
    
    # 系统 Prompt
    SYSTEM_PROMPT = """你是企业内部知识库问答助手。
请严格基于给定的参考资料回答用户问题。

要求：
1. 如果参考资料中没有相关内容，请回答"根据当前知识库无法确定该问题的答案"；
2. 不要编造不存在的信息；
3. 回答要简洁、准确、分条说明；
4. 必须给出引用来源（说明引用的文档和章节）；
5. 如果参考资料存在冲突，请说明冲突点。
"""
    
    def __init__(self, system_prompt: str = None):
        """初始化 Prompt 构造器"""
        self.system_prompt = system_prompt or self.SYSTEM_PROMPT
    
    def build_rag_prompt(
        self,
        query: str,
        retrieved_documents: List[Dict[str, Any]],
        include_citations: bool = True
    ) -> str:
        """
        构造 RAG 问答的 Prompt
        
        Args:
            query: 用户问题
            retrieved_documents: 检索到的相关文档
            include_citations: 是否在 Prompt 中包含引用信息
        
        Returns:
            构造好的 Prompt
        """
        # 构造上下文
        context = self._build_context(retrieved_documents, include_citations)
        
        # 构造完整 Prompt
        prompt = f"""{self.system_prompt}

用户问题：
{query}

参考资料：
{context}

请根据上述参考资料生成答案："""
        
        return prompt
    
    def _build_context(
        self,
        retrieved_documents: List[Dict[str, Any]],
        include_citations: bool = True
    ) -> str:
        """构造上下文"""
        
        if not retrieved_documents:
            return "没有找到相关的参考资料。"
        
        context_parts = []
        
        for i, doc in enumerate(retrieved_documents, 1):
            # 文档内容
            content = doc.get("content", "")
            
            # 元数据信息
            metadata = doc.get("metadata", {})
            file_name = metadata.get("file_name", "未知")
            section = metadata.get("section", "")
            similarity = doc.get("similarity", 0)
            
            # 构造文档块
            doc_block = f"""{i}. 【{file_name}】
内容: {content}"""
            
            if section and include_citations:
                doc_block += f"\n   章节: {section}"
            
            if include_citations:
                doc_block += f"\n   相关度: {similarity:.2%}"
            
            context_parts.append(doc_block)
        
        return "\n\n".join(context_parts)
    
    def build_multi_turn_prompt(
        self,
        conversation_history: List[Dict[str, str]],
        retrieved_documents: List[Dict[str, Any]],
        include_citations: bool = True
    ) -> str:
        """
        构造多轮对话的 Prompt
        
        Args:
            conversation_history: 对话历史 [{role: "user"/"assistant", content: "..."}, ...]
            retrieved_documents: 检索到的相关文档
            include_citations: 是否在 Prompt 中包含引用信息
        
        Returns:
            构造好的 Prompt
        """
        # 构造对话历史
        history_str = self._build_history(conversation_history)
        
        # 构造上下文
        context = self._build_context(retrieved_documents, include_citations)
        
        # 构造完整 Prompt
        prompt = f"""{self.system_prompt}

对话历史：
{history_str}

参考资料：
{context}

请根据对话历史和参考资料生成答案："""
        
        return prompt
    
    def _build_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """构造对话历史"""
        history_parts = []
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # 只显示最后 5 条消息
            if len(history_parts) < 10:  # 5 条对话
                if role == "user":
                    history_parts.append(f"用户: {content}")
                else:
                    history_parts.append(f"助手: {content}")
        
        return "\n".join(history_parts) if history_parts else "无"
    
    def build_no_answer_response(self, query: str) -> str:
        """构造"无法回答"的响应"""
        return f"""根据当前知识库无法找到与"{query}"相关的信息。

建议您：
1. 尝试使用不同的关键词重新提问
2. 联系知识库管理员补充相关文档
3. 或直接咨询相关部门同事"""
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """设置自定义系统 Prompt"""
        self.system_prompt = system_prompt
        logger.info("System prompt updated")


def get_prompt_builder(system_prompt: str = None) -> PromptBuilder:
    """获取 Prompt 构造器"""
    return PromptBuilder(system_prompt)
