import os
import asyncio
from typing import List
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from .mcp_client import get_mcp_tools, close_mcp_client
from .llm_config import init_chat_model


SYSTEM_PROMPT = """
你是一个AI智能体，可以使用工具来回答问题。

可用工具：
1. search_knowledge_base: 搜索知识库中的相关文档，参数：query（搜索词），top_k（返回数量，默认5）
2. crawl_web_content: 抓取网页内容，参数：url（网址），extract_body（是否提取正文，默认True）

工作流程：
1. 分析用户问题，判断是否需要使用工具获取信息
2. 如果需要，调用合适的工具获取信息
3. 收到工具返回的结果后，直接基于结果进行总结回答
4. 不要在收到工具结果后继续调用工具，除非结果不完整

重要规则：
- 当工具返回结果后，必须直接总结回答，不要再调用工具
- 如果工具返回了足够的信息，直接用中文总结给用户
- 如果工具没有返回有用信息，可以尝试其他工具或直接回答
"""


async def create_agent_graph(tools: List[BaseTool]):
    """
    使用StateGraph编排创建LangGraph智能体。
    
    参数:
        tools: 智能体可用的LangChain工具列表
        
    返回:
        编译后的StateGraph实例
    """
    llm = await init_chat_model()
    
    graph = create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)
    
    return graph


async def run_agent(user_query: str) -> str:
    """
    使用用户查询运行智能体并返回最终答案。
    
    参数:
        user_query: 用户的问题
        
    返回:
        最终答案字符串
    """
    try:
        tools = await get_mcp_tools()
        
        if not tools:
            return "Error: No MCP tools available. Please check if MCP servers are running."
        
        graph = await create_agent_graph(tools)
        
        initial_state = {
            "messages": [HumanMessage(content=user_query)]
        }
        
        result = await graph.ainvoke(initial_state, {"recursion_limit": 5})
        
        last_message = result["messages"][-1]
        
        if isinstance(last_message, AIMessage):
            return last_message.content
        else:
            return str(last_message)
            
    except Exception as e:
        return f"Agent execution error: {str(e)}"


async def main():
    print("Starting MCP-based AI Agent...")
    
    await get_mcp_tools()
    
    try:
        while True:
            user_input = input("User: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            print("Agent thinking...")
            response = await run_agent(user_input)
            print(f"Agent: {response}\n")
    finally:
        await close_mcp_client()


if __name__ == "__main__":
    asyncio.run(main())
