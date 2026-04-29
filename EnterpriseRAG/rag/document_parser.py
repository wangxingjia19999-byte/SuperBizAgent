"""
文档解析器 - 支持多种文件格式
"""
import os
from pathlib import Path
from typing import Dict, Any, List
import logging
import markdown
from app.core.config import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """文档解析器基类"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文档并返回内容
        
        返回格式:
        {
            "document_id": "doc_001",
            "title": "文档标题",
            "content": "完整文本内容",
            "metadata": {
                "file_type": "markdown",
                "file_name": "example.md",
                "created_at": "2026-04-29"
            }
        }
        """
        raise NotImplementedError


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果需要，可以转换 Markdown 为纯文本
            # html = markdown.markdown(content)
            # 这里保持原始 Markdown，便于保持结构
            
            file_name = Path(file_path).name
            title = file_name.replace('.md', '')
            
            return {
                "document_id": f"doc_{hash(file_path) % 10000}",
                "title": title,
                "content": content,
                "metadata": {
                    "file_type": "markdown",
                    "file_name": file_name,
                    "file_path": file_path
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse markdown file {file_path}: {str(e)}")
            raise


class TextParser(DocumentParser):
    """纯文本文档解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_name = Path(file_path).name
            title = file_name.replace('.txt', '')
            
            return {
                "document_id": f"doc_{hash(file_path) % 10000}",
                "title": title,
                "content": content,
                "metadata": {
                    "file_type": "text",
                    "file_name": file_name,
                    "file_path": file_path
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {str(e)}")
            raise


class PDFParser(DocumentParser):
    """PDF 文档解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            content = []
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                content.append(f"--- Page {page_num} ---\n{text}")
            
            full_content = "\n".join(content)
            file_name = Path(file_path).name
            title = file_name.replace('.pdf', '')
            
            return {
                "document_id": f"doc_{hash(file_path) % 10000}",
                "title": title,
                "content": full_content,
                "metadata": {
                    "file_type": "pdf",
                    "file_name": file_name,
                    "file_path": file_path,
                    "pages": len(doc)
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse PDF file {file_path}: {str(e)}")
            raise


class DocxParser(DocumentParser):
    """Word 文档解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            from docx import Document
            
            doc = Document(file_path)
            content = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    content.append(para.text)
            
            full_content = "\n".join(content)
            file_name = Path(file_path).name
            title = file_name.replace('.docx', '')
            
            return {
                "document_id": f"doc_{hash(file_path) % 10000}",
                "title": title,
                "content": full_content,
                "metadata": {
                    "file_type": "docx",
                    "file_name": file_name,
                    "file_path": file_path
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse Word file {file_path}: {str(e)}")
            raise


class DocumentParserFactory:
    """文档解析器工厂"""
    
    _parsers = {
        '.md': MarkdownParser,
        '.txt': TextParser,
        '.pdf': PDFParser,
        '.docx': DocxParser,
    }
    
    @classmethod
    def get_parser(cls, file_path: str) -> DocumentParser:
        """根据文件扩展名获取解析器"""
        ext = Path(file_path).suffix.lower()
        
        parser_class = cls._parsers.get(ext)
        if not parser_class:
            raise ValueError(f"Unsupported file type: {ext}")
        
        return parser_class()
    
    @classmethod
    def parse_document(cls, file_path: str) -> Dict[str, Any]:
        """解析文档（快捷方法）"""
        parser = cls.get_parser(file_path)
        return parser.parse(file_path)


def parse_documents(file_paths: List[str]) -> List[Dict[str, Any]]:
    """批量解析文档"""
    results = []
    for file_path in file_paths:
        try:
            doc = DocumentParserFactory.parse_document(file_path)
            results.append(doc)
            logger.info(f"Successfully parsed document: {file_path}")
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {str(e)}")
    
    return results
