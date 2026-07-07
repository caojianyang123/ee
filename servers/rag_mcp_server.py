import os
import json
from typing import List, Dict
from mcp.server.fastmcp import FastMCP

FAKE_KNOWLEDGE_BASE = [
    {
        "id": "doc-001",
        "content": "Artificial Intelligence (AI) refers to the simulation of human intelligence processes by machines, especially computer systems. These processes include learning, reasoning, and self-correction.",
        "metadata": {"category": "technology", "source": "AI Wikipedia"},
        "score": 0.95
    },
    {
        "id": "doc-002",
        "content": "Machine learning is a subset of AI that involves the use of algorithms and statistical models to enable computers to learn from data without being explicitly programmed.",
        "metadata": {"category": "technology", "source": "ML Handbook"},
        "score": 0.92
    },
    {
        "id": "doc-003",
        "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn representations of data at different levels of abstraction.",
        "metadata": {"category": "technology", "source": "Deep Learning Book"},
        "score": 0.88
    },
    {
        "id": "doc-004",
        "content": "LangChain is a framework designed to simplify the creation of applications using large language models. It provides tools for chaining different components together.",
        "metadata": {"category": "framework", "source": "LangChain Docs"},
        "score": 0.85
    },
    {
        "id": "doc-005",
        "content": "Vector databases are specialized databases designed to store and search for vector embeddings efficiently. They are commonly used in RAG (Retrieval-Augmented Generation) systems.",
        "metadata": {"category": "database", "source": "Vector DB Guide"},
        "score": 0.82
    },
    {
        "id": "doc-006",
        "content": "MCP (Model Context Protocol) is a protocol for integrating external tools and services with AI agents. It enables standardized communication between agents and tools.",
        "metadata": {"category": "protocol", "source": "MCP Spec"},
        "score": 0.78
    },
    {
        "id": "doc-007",
        "content": "LangGraph is a library for building stateful, multi-agent applications with LangChain. It allows you to model complex workflows as graphs.",
        "metadata": {"category": "framework", "source": "LangGraph Docs"},
        "score": 0.75
    },
    {
        "id": "doc-008",
        "content": "RAG (Retrieval-Augmented Generation) is a technique that combines information retrieval with generative AI to produce more accurate and grounded responses.",
        "metadata": {"category": "technique", "source": "RAG Paper"},
        "score": 0.72
    }
]

AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "default-token-12345")
PORT = int(os.environ.get("PORT", 8001))

server = FastMCP(
    name="RAG Knowledge Base Server",
    instructions="Search knowledge base for relevant documents.",
    port=PORT
)


def auth_middleware(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "Unauthorized: Missing Bearer token"}
    token = auth_header[7:]
    if token != AUTH_TOKEN:
        return {"error": "Unauthorized: Invalid token"}
    return None


@server.tool(
    name="search_knowledge_base",
    description="搜索知识库中与查询相关的文档"
)
async def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """
    搜索知识库中与查询相关的文档。
    
    参数:
        query: 搜索查询字符串
        top_k: 返回结果数量（默认：5）
    
    返回:
        JSON字符串，包含文档ID、内容、元数据和相关性分数
    """
    query_lower = query.lower()
    matched_docs = []
    
    for doc in FAKE_KNOWLEDGE_BASE:
        if (query_lower in doc["content"].lower() or
            query_lower in doc["metadata"].get("category", "").lower() or
            query_lower in doc["metadata"].get("source", "").lower()):
            matched_docs.append(doc)
    
    matched_docs.sort(key=lambda x: x["score"], reverse=True)
    results = matched_docs[:top_k]
    
    return json.dumps({"results": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    server.run(transport="sse")
