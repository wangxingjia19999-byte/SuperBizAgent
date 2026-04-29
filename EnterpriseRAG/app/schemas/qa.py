"""
API 数据结构定义
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 问答接口 ============

class CitationSchema(BaseModel):
    """引用来源"""
    document_name: str = Field(..., description="文档名")
    section: str = Field("", description="章节")
    similarity: float = Field(..., description="相关度")


class QARequestSchema(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="会话ID")
    top_k: Optional[int] = Field(None, description="检索数量")


class QAResponseSchema(BaseModel):
    """问答响应"""
    query: str = Field(..., description="用户问题")
    answer: str = Field(..., description="系统回答")
    citations: List[CitationSchema] = Field(..., description="引用来源")
    confidence: float = Field(..., description="置信度 (0-1)")
    retrieval_count: int = Field(..., description="检索到的文档数")


# ============ 文档接口 ============

class DocumentUploadSchema(BaseModel):
    """文档上传请求"""
    category: str = Field("general", description="文档分类")
    permission_scope: Optional[str] = Field(None, description="权限范围")


class DocumentSchema(BaseModel):
    """文档信息"""
    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    category: str = Field(..., description="分类")
    status: str = Field(..., description="处理状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DocumentListSchema(BaseModel):
    """文档列表"""
    total: int = Field(..., description="文档总数")
    documents: List[DocumentSchema] = Field(..., description="文档列表")


# ============ 会话接口 ============

class MessageSchema(BaseModel):
    """消息"""
    role: str = Field(..., description="发送者角色: user/assistant")
    content: str = Field(..., description="消息内容")
    citations: Optional[List[CitationSchema]] = Field(None, description="引用来源")


class SessionSchema(BaseModel):
    """会话"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    messages: List[MessageSchema] = Field(..., description="消息列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ============ 反馈接口 ============

class FeedbackSchema(BaseModel):
    """用户反馈"""
    message_id: str = Field(..., description="对应消息ID")
    feedback_type: str = Field(
        ...,
        description="反馈类型: helpful/not_helpful/answer_wrong/citation_wrong/outdated"
    )
    comment: Optional[str] = Field(None, description="反馈说明")


class FeedbackResponseSchema(BaseModel):
    """反馈响应"""
    feedback_id: str = Field(..., description="反馈ID")
    message: str = Field(..., description="反馈成功提示")


# ============ 错误响应 ============

class ErrorSchema(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")


# ============ 通用响应 ============

class SuccessSchema(BaseModel):
    """成功响应"""
    message: str = Field(..., description="成功信息")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")
