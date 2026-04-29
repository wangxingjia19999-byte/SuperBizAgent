"""
文本切分模块 - 将长文档分割为小的文本块
"""
from typing import List, Dict, Any
import logging
import re
from app.core.config import get_logger

logger = get_logger(__name__)


class TextSplitter:
    """文本切分器基类"""
    
    def split(self, text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
        """
        分割文本
        
        返回格式:
        [
            {
                "chunk_id": "chunk_001",
                "content": "文本内容",
                "page": 1,
                "section": "章节名"
            }
        ]
        """
        raise NotImplementedError


class RecursiveCharacterSplitter(TextSplitter):
    """递归字符切分器 - 优先按标题切分"""
    
    def split(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        递归切分文本
        优先级：标题 > 段落 > 句子 > 字符
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        chunk_id = 0
        
        # 第一步：按标题切分（Markdown 标题）
        header_splits = self._split_by_headers(text)
        
        for section_content, section_info in header_splits:
            # 第二步：按段落切分
            paragraph_splits = section_content.split('\n\n')
            
            current_chunk = ""
            for paragraph in paragraph_splits:
                # 检查是否需要创建新 chunk
                if len(current_chunk) + len(paragraph) > chunk_size:
                    if current_chunk:
                        chunks.append(self._create_chunk(
                            current_chunk,
                            chunk_id,
                            section_info,
                            metadata
                        ))
                        chunk_id += 1
                        
                        # 添加重叠内容
                        current_chunk = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""
                
                current_chunk += paragraph + "\n\n"
            
            # 添加最后一个 chunk
            if current_chunk.strip():
                chunks.append(self._create_chunk(
                    current_chunk,
                    chunk_id,
                    section_info,
                    metadata
                ))
                chunk_id += 1
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _split_by_headers(self, text: str) -> List[tuple]:
        """按 Markdown 标题分割"""
        # 匹配 Markdown 标题 # ## ### 等
        header_pattern = r'^(#{1,6})\s+(.+)$'
        
        lines = text.split('\n')
        sections = []
        current_section = []
        current_header = None
        
        for line in lines:
            match = re.match(header_pattern, line, re.MULTILINE)
            if match:
                # 如果有内容，保存为一个 section
                if current_section:
                    sections.append(('\n'.join(current_section), current_header))
                
                level = len(match.group(1))
                header_text = match.group(2)
                current_header = {"title": header_text, "level": level}
                current_section = [line]
            else:
                current_section.append(line)
        
        # 添加最后一个 section
        if current_section:
            sections.append(('\n'.join(current_section), current_header))
        
        return sections
    
    def _create_chunk(
        self,
        content: str,
        chunk_id: int,
        section_info: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建一个 chunk"""
        return {
            "chunk_id": f"chunk_{chunk_id:04d}",
            "content": content.strip(),
            "section": section_info.get("title", "") if section_info else "",
            "section_level": section_info.get("level", 0) if section_info else 0,
            "page": metadata.get("page", 0),
            "file_name": metadata.get("file_name", ""),
            "document_id": metadata.get("document_id", ""),
        }


class SimpleSplitter(TextSplitter):
    """简单切分器 - 按固定数量字符切分"""
    
    def split(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """简单按字符数切分"""
        
        if metadata is None:
            metadata = {}
        
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(text), chunk_size - chunk_overlap):
            content = text[i:i + chunk_size]
            if content.strip():
                chunks.append({
                    "chunk_id": f"chunk_{chunk_id:04d}",
                    "content": content.strip(),
                    "section": "",
                    "page": metadata.get("page", 0),
                    "file_name": metadata.get("file_name", ""),
                    "document_id": metadata.get("document_id", ""),
                })
                chunk_id += 1
        
        return chunks


def split_documents_to_chunks(
    documents: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    use_recursive: bool = True
) -> List[Dict[str, Any]]:
    """
    将文档列表转换为 chunks
    
    Args:
        documents: 文档列表 (来自 DocumentParser)
        chunk_size: 每个 chunk 的大小
        chunk_overlap: chunk 之间的重叠
        use_recursive: 是否使用递归切分
    
    Returns:
        chunks 列表
    """
    all_chunks = []
    
    splitter = RecursiveCharacterSplitter() if use_recursive else SimpleSplitter()
    
    for doc in documents:
        chunks = splitter.split(
            text=doc["content"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            metadata={
                "document_id": doc.get("document_id", ""),
                "file_name": doc.get("metadata", {}).get("file_name", ""),
                "page": 0
            }
        )
        all_chunks.extend(chunks)
    
    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks
