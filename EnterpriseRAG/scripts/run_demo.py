"""
演示脚本 - 展示完整的 RAG 流程
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.config import settings, init_directories, get_logger
from rag.document_parser import DocumentParserFactory
from rag.text_splitter import split_documents_to_chunks
from rag.embeddings import embed_chunks, get_embedding_provider
from infrastructure.vector.chroma_store import add_chunks_to_vector_store, get_vector_store
from rag.qa_chain import get_qa_chain

# 初始化
init_directories()
logger = get_logger(__name__)


def create_sample_documents():
    """创建示例文档"""
    
    # 创建示例 Markdown 文档
    sample_md = """# 生产发布规范

## 1. 发布前准备

发布前需要完成以下准备工作：

### 1.1 代码审批
- 所有代码必须通过 Code Review
- 至少 2 个 Reviewer 的同意
- 修改内容需要有清晰的 PR 描述

### 1.2 测试验证
- 完成单元测试，覆盖率 ≥ 80%
- 完成集成测试
- 在测试环境完全验证功能

### 1.3 发布审批
- 获取服务负责人的签核
- 获取 SRE 团队的确认
- 获取产品负责人的确认

## 2. 发布流程

### 2.1 发布前检查清单
- [ ] 确认版本号
- [ ] 确认发布说明
- [ ] 确认回滚计划
- [ ] 通知相关人员

### 2.2 灰度发布
1. 10% 流量灰度，观察 5 分钟
2. 30% 流量灰度，观察 10 分钟
3. 100% 全量发布

### 2.3 发布后验证
- 检查错误率
- 检查延迟指标
- 检查关键业务指标
- 持续观察 30 分钟

## 3. 异常处理

### 3.1 发布失败处理
1. 立即判断故障等级
2. 通知所有相关人员
3. 评估回滚和快速修复的可行性
4. 执行回滚或快速修复
5. 事后分析和改进

### 3.2 性能问题处理
- 如果 CPU 增长 ≥ 50%，立即回滚
- 如果错误率增长 ≥ 1%，立即回滚
- 如果 P99 延迟增长 ≥ 100ms，需要评估

## 4. 发布历史查询
可在发布管理系统查询历史发布记录。
"""
    
    sample_md_path = settings.UPLOAD_DIR / "生产发布规范.md"
    with open(sample_md_path, 'w', encoding='utf-8') as f:
        f.write(sample_md)
    
    print(f"✅ Created sample document: {sample_md_path}")
    return [str(sample_md_path)]


def demo_document_parsing(file_paths):
    """演示文档解析"""
    print("\n📄 Step 1: Document Parsing")
    print("-" * 50)
    
    documents = []
    for file_path in file_paths:
        try:
            doc = DocumentParserFactory.parse_document(file_path)
            documents.append(doc)
            print(f"✅ Parsed: {doc['metadata']['file_name']}")
            print(f"   Title: {doc['title']}")
            print(f"   Content length: {len(doc['content'])} characters")
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {str(e)}")
    
    return documents


def demo_text_splitting(documents):
    """演示文本切分"""
    print("\n✂️  Step 2: Text Splitting")
    print("-" * 50)
    
    chunks = split_documents_to_chunks(
        documents,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    
    print(f"✅ Total chunks: {len(chunks)}")
    print(f"   Chunk size: {settings.CHUNK_SIZE} characters")
    print(f"   Overlap: {settings.CHUNK_OVERLAP} characters")
    
    # 显示前 3 个 chunks
    print("\n   Sample chunks:")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n   Chunk {i}: {chunk['chunk_id']}")
        print(f"   Section: {chunk['section']}")
        print(f"   Content: {chunk['content'][:100]}...")
    
    return chunks


def demo_embedding(chunks):
    """演示向量化"""
    print("\n🔢 Step 3: Embedding Generation")
    print("-" * 50)
    
    embedding_provider = get_embedding_provider("local")
    chunks = embed_chunks(chunks, embedding_provider)
    
    print(f"✅ Generated embeddings for {len(chunks)} chunks")
    print(f"   Embedding model: all-MiniLM-L6-v2")
    print(f"   Embedding dimension: {len(chunks[0]['embedding'])}")
    print(f"   Sample embedding (first 5 values):")
    print(f"   {chunks[0]['embedding'][:5]}")
    
    return chunks


def demo_indexing(chunks):
    """演示索引构建"""
    print("\n📚 Step 4: Vector Store Indexing")
    print("-" * 50)
    
    vector_store = get_vector_store()
    add_chunks_to_vector_store(chunks, vector_store)
    
    print(f"✅ Added {len(chunks)} chunks to vector store")
    print(f"   Vector store type: Chroma")
    print(f"   Persistence dir: {settings.CHROMA_PERSIST_DIR}")


def demo_retrieval_and_qa():
    """演示检索和问答"""
    print("\n🔍 Step 5: Retrieval and QA")
    print("-" * 50)
    
    # 创建 QA 链
    qa_chain = get_qa_chain(use_mock=True)  # 使用 mock LLM 进行演示
    
    # 示例问题
    test_questions = [
        "生产环境发布前需要哪些审批？",
        "发布失败后应该怎么办？",
        "灰度发布的步骤是什么？"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)
        
        result = qa_chain.answer(question)
        
        print(f"💬 Answer:\n{result['answer']}\n")
        print(f"📌 Citations:")
        for citation in result['citations']:
            print(f"   - Document: {citation['document_name']}")
            print(f"     Section: {citation['section']}")
            print(f"     Similarity: {citation['similarity']:.2%}")
        
        print(f"📊 Metrics:")
        print(f"   - Confidence: {result['confidence']:.2%}")
        print(f"   - Retrieved documents: {result['retrieval_count']}")


def main():
    """主函数"""
    print("=" * 60)
    print("  🚀 Enterprise RAG System - Complete Workflow Demo")
    print("=" * 60)
    
    try:
        # Step 1: 创建示例文档
        print("\n📝 Creating sample documents...")
        file_paths = create_sample_documents()
        
        # Step 2: 文档解析
        documents = demo_document_parsing(file_paths)
        if not documents:
            print("❌ No documents to process")
            return
        
        # Step 3: 文本切分
        chunks = demo_text_splitting(documents)
        if not chunks:
            print("❌ No chunks to process")
            return
        
        # Step 4: 向量化
        chunks = demo_embedding(chunks)
        
        # Step 5: 索引构建
        demo_indexing(chunks)
        
        # Step 6: 检索和问答
        demo_retrieval_and_qa()
        
        print("\n" + "=" * 60)
        print("  ✅ Demo completed successfully!")
        print("=" * 60)
        print("\n📚 Next steps:")
        print("   1. Run FastAPI server: python main.py")
        print("   2. Visit http://localhost:8000/docs for API documentation")
        print("   3. Upload documents via /api/v1/documents/upload")
        print("   4. Ask questions via /api/v1/qa/ask")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
