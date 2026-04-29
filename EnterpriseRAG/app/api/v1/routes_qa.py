"""
问答 API 路由
"""
from typing import Optional, List
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.config import get_logger
from app.schemas.qa import (
    QARequestSchema, QAResponseSchema, CitationSchema,
    MessageSchema, SessionSchema, ErrorSchema
)
from rag.qa_chain import get_qa_chain

logger = get_logger(__name__)

router = APIRouter(prefix="/qa", tags=["QA"])

# 简单的会话存储（实际项目中应该使用数据库）
_sessions = {}


@router.post("/ask", response_model=QAResponseSchema)
async def ask_question(request: QARequestSchema):
    """
    提问接口 - 单轮问答
    
    Args:
        question: 用户问题
        session_id: 可选的会话ID
        top_k: 可选的检索数量
    
    Returns:
        问答结果
    """
    try:
        # 获取 QA 链
        qa_chain = get_qa_chain(use_mock=True)  # 演示使用 mock LLM
        
        # 执行问答
        result = qa_chain.answer(
            query=request.question,
            top_k=request.top_k
        )
        
        # 转换为 API 响应格式
        response = QAResponseSchema(
            query=result["query"],
            answer=result["answer"],
            citations=[
                CitationSchema(
                    document_name=c["document_name"],
                    section=c["section"],
                    similarity=c["similarity"]
                )
                for c in result["citations"]
            ],
            confidence=result["confidence"],
            retrieval_count=result["retrieval_count"]
        )
        
        logger.info(f"User question answered: {request.question[:50]}")
        return response
    
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/sessions/{session_id}/ask", response_model=QAResponseSchema)
async def ask_with_session(session_id: str, request: QARequestSchema):
    """
    在会话中提问 - 支持多轮对话
    
    Args:
        session_id: 会话ID
        question: 用户问题
    
    Returns:
        问答结果
    """
    try:
        # 获取或创建会话
        if session_id not in _sessions:
            _sessions[session_id] = {
                "session_id": session_id,
                "title": request.question[:50],
                "messages": []
            }
        
        session = _sessions[session_id]
        
        # 获取对话历史
        history = session.get("messages", [])
        
        # 获取 QA 链
        qa_chain = get_qa_chain(use_mock=True)
        
        # 执行多轮问答
        result = qa_chain.answer_with_history(
            query=request.question,
            conversation_history=history,
            top_k=request.top_k
        )
        
        # 添加到会话历史
        session["messages"].append({
            "role": "user",
            "content": request.question
        })
        session["messages"].append({
            "role": "assistant",
            "content": result["answer"],
            "citations": result["citations"]
        })
        
        # 返回响应
        response = QAResponseSchema(
            query=result["query"],
            answer=result["answer"],
            citations=[
                CitationSchema(
                    document_name=c["document_name"],
                    section=c["section"],
                    similarity=c["similarity"]
                )
                for c in result["citations"]
            ],
            confidence=result["confidence"],
            retrieval_count=result["retrieval_count"]
        )
        
        logger.info(f"Session {session_id}: question answered")
        return response
    
    except Exception as e:
        logger.error(f"Error in ask_with_session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"多轮问答失败: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=List[MessageSchema])
async def get_session_messages(session_id: str):
    """
    获取会话历史
    
    Args:
        session_id: 会话ID
    
    Returns:
        消息列表
    """
    try:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        session = _sessions[session_id]
        messages = session.get("messages", [])
        
        return [
            MessageSchema(
                role=msg["role"],
                content=msg["content"],
                citations=msg.get("citations")
            )
            for msg in messages
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_session_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话历史失败: {str(e)}")


@router.get("/sessions", response_model=List[dict])
async def list_sessions():
    """
    列出所有会话
    
    Returns:
        会话列表
    """
    try:
        sessions = []
        for session_id, session in _sessions.items():
            sessions.append({
                "session_id": session_id,
                "title": session.get("title", ""),
                "message_count": len(session.get("messages", []))
            })
        return sessions
    except Exception as e:
        logger.error(f"Error in list_sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    
    Args:
        session_id: 会话ID
    
    Returns:
        成功消息
    """
    try:
        if session_id in _sessions:
            del _sessions[session_id]
            logger.info(f"Session {session_id} deleted")
            return {"message": "会话已删除"}
        else:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "QA API is running"}
