import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

class FinalAnswer(BaseModel):
    """
    Agent最终回答的结构化输出模型。
    """
    thought: str = Field(description="回答背后的推理过程")
    answer: str = Field(description="用户问题的最终答案")


async def init_chat_model():
    """
    使用阿里云百炼 OpenAI 兼容 API 初始化聊天模型。
    
    返回:
        配置好的 ChatOpenAI 实例
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    
    llm = ChatOpenAI(
        model="qwen3.7-plus",
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=4096
    )
    
    return llm


async def init_structured_llm():
    """
    初始化支持结构化输出的聊天模型。
    
    返回:
        配置为结构化输出的 ChatOpenAI 实例
    """
    llm = await init_chat_model()
    structured_llm = llm.with_structured_output(FinalAnswer)
    return structured_llm
