import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from typing import List, Optional

AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "default-token-12345")

RAG_SERVER_URL = os.environ.get("RAG_SERVER_URL", "http://localhost:8001/sse")
CRAWLER_SERVER_URL = os.environ.get("CRAWLER_SERVER_URL", "http://localhost:8002/sse")

_client: Optional[MultiServerMCPClient] = None
_tools: Optional[List[BaseTool]] = None


def create_mcp_client_config() -> dict:
    """
    创建 MultiServerMCPClient 的配置字典。
    
    返回:
        MCP服务器连接的配置字典
    """
    return {
        "rag": {
            "transport": "sse",
            "url": RAG_SERVER_URL,
            "headers": {"Authorization": f"Bearer {AUTH_TOKEN}"}
        },
        "crawler": {
            "transport": "sse",
            "url": CRAWLER_SERVER_URL,
            "headers": {"Authorization": f"Bearer {AUTH_TOKEN}"}
        }
    }


async def init_mcp_client() -> List[BaseTool]:
    """
    初始化MCP客户端并在整个会话期间保持连接打开。
    
    返回:
        LangChain BaseTool实例列表
    """
    global _client, _tools
    
    if _client is None:
        try:
            print(f"Connecting to RAG server: {RAG_SERVER_URL}")
            print(f"Connecting to Crawler server: {CRAWLER_SERVER_URL}")
            print(f"Auth token: {AUTH_TOKEN[:10]}...")
            
            _client = MultiServerMCPClient(create_mcp_client_config())
            await _client.__aenter__()
            
            _tools = _client.get_tools()
            print(f"Retrieved {len(_tools)} tools: {[t.name for t in _tools]}")
        except Exception as e:
            import traceback
            print(f"Error initializing MCP client: {e}")
            traceback.print_exc()
            _tools = []
    
    return _tools if _tools else []


async def get_mcp_tools() -> List[BaseTool]:
    """
    从连接的MCP服务器获取所有工具。
    
    返回:
        LangChain BaseTool实例列表
    """
    return await init_mcp_client()


async def close_mcp_client():
    """
    关闭MCP客户端连接。
    """
    global _client
    if _client is not None:
        await _client.__aexit__(None, None, None)
        _client = None
        print("MCP client connection closed")
