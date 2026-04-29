# 企业级 RAG 知识库问答系统

基于 RAG (Retrieval-Augmented Generation) 技术的企业内部知识库智能问答系统。

## 📚 项目特性

- ✅ **完整的 RAG 流程**: 文档解析 → 文本切分 → 向量化 → 检索 → 问答生成
- ✅ **多格式文档支持**: Markdown, TXT, PDF, Word (可扩展)
- ✅ **向量检索**: 使用 Chroma 进行高效的语义检索
- ✅ **本地 Embedding**: 使用 sentence-transformers 生成向量
- ✅ **多轮对话**: 支持连续追问和上下文理解
- ✅ **答案溯源**: 每个回答都标注来源文档和相似度
- ✅ **FastAPI 框架**: 现代异步 Web 框架
- ✅ **完整 API 文档**: 自动生成的 OpenAPI/Swagger 文档

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- pip

### 2. 安装依赖

```bash
# 复制 .env.example 为 .env
cp .env.example .env

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 运行演示

演示脚本展示完整的 RAG 流程：

```bash
python scripts/run_demo.py
```

输出示例：

```
============================================================
  🚀 Enterprise RAG System - Complete Workflow Demo
============================================================

📝 Creating sample documents...
✅ Created sample document: data/uploads/生产发布规范.md

📄 Step 1: Document Parsing
--------------------------------------------------
✅ Parsed: 生产发布规范.md
   Title: 生产发布规范
   Content length: 2345 characters

... (更多输出)

❓ Question: 生产环境发布前需要哪些审批？
--------------------------------------------------
💬 Answer:
生产环境发布前需要完成代码评审、测试验证和负责人审批。

📌 Citations:
   - Document: 生产发布规范.md
     Section: 1.3 发布审批
     Similarity: 85.24%
```

### 4. 启动 API 服务

```bash
# 开发环境（自动重载）
python -m uvicorn main:app --reload

# 或直接运行
python main.py
```

访问 API 文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 API 使用示例

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@生产发布规范.pdf" \
  -F "category=规范" \
  -F "permission_scope=all"
```

响应：

```json
{
  "document_id": "doc_a1b2c3d4",
  "file_name": "生产发布规范.pdf",
  "status": "UPLOADED",
  "message": "文档上传成功，准备处理..."
}
```

### 构建文档索引

```bash
curl -X POST "http://localhost:8000/api/v1/documents/index/doc_a1b2c3d4"
```

响应：

```json
{
  "document_id": "doc_a1b2c3d4",
  "status": "READY",
  "chunk_count": 15,
  "message": "文档索引构建完成"
}
```

### 提问

```bash
curl -X POST "http://localhost:8000/api/v1/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "生产环境发布前需要哪些审批？",
    "top_k": 3
  }'
```

响应：

```json
{
  "query": "生产环境发布前需要哪些审批？",
  "answer": "生产环境发布前需要完成代码评审、测试验证和负责人审批...",
  "citations": [
    {
      "document_name": "生产发布规范.pdf",
      "section": "1.3 发布审批",
      "similarity": 0.8524
    }
  ],
  "confidence": 0.8524,
  "retrieval_count": 3
}
```

### 多轮对话

```bash
# 创建会话继续提问
curl -X POST "http://localhost:8000/api/v1/qa/sessions/sess_001/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如果是紧急修复还需要这些审批吗？"
  }'
```

## 📁 项目结构

```
enterprise-rag-qa/
├── main.py                          # FastAPI 主入口
├── requirements.txt                 # 依赖列表
├── .env.example                     # 环境变量模板
│
├── app/
│   ├── core/
│   │   ├── config.py               # 配置管理
│   │   ├── security.py             # 安全相关（待实现）
│   │   └── logging.py              # 日志配置
│   │
│   ├── api/v1/
│   │   ├── router.py               # API 总路由
│   │   ├── routes_qa.py            # 问答路由
│   │   ├── routes_documents.py     # 文档管理路由
│   │   ├── routes_feedback.py      # 反馈路由（待实现）
│   │   └── routes_audit.py         # 审计路由（待实现）
│   │
│   └── schemas/
│       ├── qa.py                   # 数据模型定义
│       ├── document.py             # 文档模型（待实现）
│       └── ...
│
├── rag/
│   ├── document_parser.py          # 文档解析（支持 MD, TXT, PDF, DOCX）
│   ├── text_splitter.py            # 文本切分
│   ├── embeddings.py               # 向量生成
│   ├── vector_store.py             # 向量存储接口（待实现）
│   ├── retriever.py                # 检索（向量+混合）
│   ├── reranker.py                 # Reranker（待实现）
│   ├── prompt_builder.py           # Prompt 构造
│   └── qa_chain.py                 # QA 链总编排
│
├── services/
│   ├── auth_service.py             # 认证服务（待实现）
│   ├── document_service.py         # 文档服务（待实现）
│   ├── qa_service.py               # 问答服务（待实现）
│   ├── feedback_service.py         # 反馈服务（待实现）
│   └── audit_service.py            # 审计服务（待实现）
│
├── infrastructure/
│   ├── db/
│   │   ├── session.py              # 数据库连接（待实现）
│   │   ├── models.py               # SQLAlchemy 模型（待实现）
│   │   └── repositories.py         # 数据操作层（待实现）
│   │
│   ├── vector/
│   │   ├── chroma_store.py         # Chroma 实现
│   │   └── pgvector_store.py       # PGVector 实现（待实现）
│   │
│   └── storage/
│       ├── local_storage.py        # 本地文件存储
│       └── minio_storage.py        # MinIO 存储（待实现）
│
├── security/
│   ├── rbac.py                     # RBAC 权限管理（待实现）
│   ├── permission_checker.py       # 权限检查（待实现）
│   └── masking.py                  # 敏感信息脱敏（待实现）
│
├── tasks/
│   ├── document_index_task.py      # 异步索引任务（待实现）
│   └── cleanup_task.py             # 清理任务（待实现）
│
├── data/
│   ├── uploads/                    # 上传文档存储
│   ├── samples/                    # 示例数据
│   └── chroma/                     # Chroma 数据库
│
├── scripts/
│   ├── run_demo.py                 # 完整流程演示
│   ├── init_db.py                  # 数据库初始化（待实现）
│   └── build_index.py              # 批量索引构建（待实现）
│
└── tests/
    ├── test_document_parser.py     # 文档解析测试
    ├── test_retriever.py           # 检索测试
    ├── test_qa.py                  # 问答测试
    └── test_permission.py          # 权限测试（待实现）
```

## 📋 第一阶段完成情况

✅ **已完成**：
- [x] 配置管理系统
- [x] 多格式文档解析 (Markdown, TXT, PDF, Word)
- [x] 智能文本切分 (递归切分)
- [x] 向量化 (本地 Embedding)
- [x] 向量存储 (Chroma)
- [x] 检索 (向量检索 + 混合检索)
- [x] Prompt 构造
- [x] QA 链编排
- [x] FastAPI 框架
- [x] 完整 API 接口
- [x] 多轮对话支持
- [x] 演示脚本

📝 **待完成（第二阶段及后续）**：
- [ ] PostgreSQL 集成
- [ ] JWT 认证
- [ ] RBAC 权限管理
- [ ] 审计日志
- [ ] 反馈系统
- [ ] 异步任务队列
- [ ] 前端界面
- [ ] 企业系统集成

## 🔧 配置说明

### 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `CHUNK_SIZE` | 文本块大小 | 500 |
| `CHUNK_OVERLAP` | 文本块重叠 | 100 |
| `RETRIEVER_TOP_K` | 检索文档数 | 3 |
| `SIMILARITY_THRESHOLD` | 相似度阈值 | 0.3 |
| `LLM_TEMPERATURE` | 生成温度 | 0.7 |
| `LLM_MAX_TOKENS` | 最大生成长度 | 1000 |

### 向量数据库切换

**切换到 OpenAI Embedding**：

```python
# 在 embeddings.py 中
provider = get_embedding_provider("openai")  # 而不是 "local"
```

**切换到其他 LLM**：

```python
# 修改 .env
LLM_MODEL=gpt-3.5-turbo
# 或在代码中
llm_provider = OpenAIProvider(model="gpt-3.5-turbo")
```

## 🧪 测试

运行单元测试（待实现）：

```bash
pytest tests/
```

## 📦 部署

### Docker 部署

```bash
docker build -t enterprise-rag .
docker run -p 8000:8000 enterprise-rag
```

### Docker Compose 部署（待实现）

```bash
docker-compose up -d
```

## 📚 相关文档

- [设计报告](设计报告.md) - 完整的系统设计文档
- [API 文档](http://localhost:8000/docs) - 自动生成的 API 文档
- [技术文档] - 各模块详细文档（待补充）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💼 作者

基于企业 RAG 系统设计报告实现

---

## 🆘 遇到问题？

### 常见问题

**Q: ImportError: No module named 'chromadb'**

A: 运行 `pip install -r requirements.txt` 安装依赖

**Q: 如何使用 OpenAI API？**

A: 
1. 在 `.env` 中设置 `OPENAI_API_KEY`
2. 在 `qa_chain.py` 中使用 `OpenAIProvider` 而不是 `MockLLMProvider`

**Q: 向量库数据在哪里？**

A: 默认存储在 `data/chroma/` 目录

**Q: 如何清空向量库重新开始？**

A: 删除 `data/chroma/` 文件夹

### 获取帮助

- 查看日志文件：`logs/` 目录
- 检查配置：`.env` 文件
- 运行演示脚本确保环境正确

## 🗺️ 路线图

- [ ] 第二阶段：数据库 + 权限管理
- [ ] 第三阶段：多轮对话优化
- [ ] 第四阶段：企业系统集成
- [ ] 前端 Web UI
- [ ] 移动客户端
- [ ] 知识库管理后台

---

**祝你使用愉快！ 🎉**
