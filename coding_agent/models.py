"""数据模型定义，包含 LLM 配置与工具调用结构。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LLMConfig:
    """LLM 连接配置，包含模型、密钥与网关信息。

    属性：
        provider: LLM 提供者标识（例如 'glm4.7' 或 'deepseek'）
        api_key: 对应提供者的 API 密钥
        model: 模型名称
        base_url: API 基础地址
        temperature: 采样温度
        max_tokens: 单次响应的最大 token 数
    """

    provider: str
    api_key: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int


@dataclass
class ToolInvocation:
    """工具调用信息，保存工具名与参数。

    属性：
        tool_name: 工具名称（如 'read_file'、'edit_file' 等）
        args: 工具调用的参数字典
    """

    tool_name: str
    args: Dict[str, Any]
