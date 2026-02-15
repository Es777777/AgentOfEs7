"""LLM 客户端封装，负责与模型交互。"""

from typing import Dict, List

from openai import OpenAI

from coding_agent.models import LLMConfig


def build_llm_client(config: LLMConfig) -> OpenAI:
    """使用配置生成 OpenAI 兼容客户端。"""

    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def execute_llm_call(conversation: List[Dict[str, str]], client: OpenAI, config: LLMConfig) -> str:
    """发送对话到指定 LLM 并返回文本回复。"""

    response = client.chat.completions.create(
        model=config.model,
        messages=conversation,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
    return response.choices[0].message.content
