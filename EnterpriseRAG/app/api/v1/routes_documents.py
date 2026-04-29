"""
文档管理 API 路由
"""
import uuid
from typing import List
from pathlib import Path
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.config import get_logger, settings
from app.schemas.qa import DocumentSchema, DocumentListSchema, SuccessSchema
from rag.document_parser import DocumentParserFactory
from rag.text_splitter import split_documents_to_chunks
from rag.embeddings import embed_chunks, get_embedding_provider
from infrastructure.vector.chroma_store import add_chunks_to_vector_store, get_vector_store

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

# 简单的文档存储（实际项目中应该使用数据库）
_documents = {}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general"),
    permission_scope: str = Form("all")
):
    """
    上传文档
    
    Args:
        file: 文档文件
        category: 文档分类
        permission_scope: 权限范围
    
    Returns:
        上传结果
    """
    try:
        # 生成文档 ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # 保存文件
        file_path = settings.UPLOAD_DIR / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {doc_id}")
        
        # 创建文档记录
        doc_record = {
            "document_id": doc_id,
            "title": file.filename.split('.')[0],
            "file_name": file.filename,
            "file_path": str(file_path),
            "file_type": file.filename.split('.')[-1].lower(),
            "category": category,
            "permission_scope": permission_scope,
            "status": "UPLOADED"
        }
        
        _documents[doc_id] = doc_record
        
        return {
            "document_id": doc_id,
            "file_name": file.filename,
            "status": "UPLOADED",
            "message": "文档上传成功，准备处理..."
        }
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/index/{document_id}")
async def build_document_index(document_id: str):
    """
    构建文档索引
    
    Args:
        document_id: 文档ID
    
    Returns:
        索引构建结果
    """
    try:
        if document_id not in _documents:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")
        
        doc_record = _documents[document_id]
        file_path = doc_record["file_path"]
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="文档文件不存在")
        
        # 更新状态为处理中
        doc_record["status"] = "PARSING"
        
        try:
            # 1. 解析文档
            logger.info(f"Parsing document: {file_path}")
            parsed_doc = DocumentParserFactory.parse_document(file_path)
            
            # 2. 切分文本
            logger.info(f"Splitting document into chunks")
            chunks = split_documents_to_chunks(
                [parsed_doc],
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # 3. 生成 Embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embedding_provider = get_embedding_provider("local")
            chunks = embed_chunks(chunks, embedding_provider)
            
            # 4. 添加到向量库
            logger.info(f"Adding chunks to vector store")
            add_chunks_to_vector_store(chunks, get_vector_store())
            
            # 5. 更新状态为完成
            doc_record["status"] = "READY"
            doc_record["chunk_count"] = len(chunks)
            
            logger.info(f"Document {document_id} indexed successfully")
            
            return {
                "document_id": document_id,
                "status": "READY",
                "chunk_count": len(chunks),
                "message": "文档索引构建完成"
            }
        
        except Exception as e:
            doc_record["status"] = "FAILED"
            doc_record["error"] = str(e)
            logger.error(f"Failed to index document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"索引构建失败: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in build_document_index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(document_id: str):
    """
    获取文档信息
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档信息
    """
    try:
        if document_id not in _documents:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")
        
        doc = _documents[document_id]
        
        return DocumentSchema(
            document_id=doc["document_id"],
            title=doc["title"],
            file_name=doc["file_name"],
            file_type=doc["file_type"],
            category=doc["category"],
            status=doc["status"],
            created_at="2026-04-29T00:00:00",
            updated_at="2026-04-29T00:00:00"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")


@router.get("")
async def list_documents(
    category: str = None,
    status: str = None
):
    """
    列出文档
    
    Args:
        category: 文档分类过滤
        status: 状态过滤
    
    Returns:
        文档列表
    """
    try:
        docs = list(_documents.values())
        
        # 应用过滤
        if category:
            docs = [d for d in docs if d.get("category") == category]
        if status:
            docs = [d for d in docs if d.get("status") == status]
        
        return {
            "total": len(docs),
            "documents": [
                {
                    "document_id": d["document_id"],
                    "title": d["title"],
                    "file_name": d["file_name"],
                    "file_type": d["file_type"],
                    "category": d["category"],
                    "status": d["status"],
                    "chunk_count": d.get("chunk_count", 0),
                    "created_at": "2026-04-29T00:00:00",
                    "updated_at": "2026-04-29T00:00:00"
                }
                for d in docs
            ]
        }
    except Exception as e:
        logger.error(f"Error in list_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列表查询失败: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    
    Args:
        document_id: 文档ID
    
    Returns:
        删除结果
    """
    try:
        if document_id not in _documents:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")
        
        doc = _documents[document_id]
        
        # 删除文件
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        
        # 从向量库删除（这里简化处理）
        # 实际项目中应该根据 document_id 删除相关的 chunks
        
        # 删除记录
        del _documents[document_id]
        logger.info(f"Deleted document record: {document_id}")
        
        return {"message": f"文档已删除: {document_id}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/{document_id}/reindex")
async def reindex_document(document_id: str):
    """
    重新索引文档
    
    Args:
        document_id: 文档ID
    
    Returns:
        重新索引结果
    """
    # 实现与 build_document_index 几乎相同
    return await build_document_index(document_id)
