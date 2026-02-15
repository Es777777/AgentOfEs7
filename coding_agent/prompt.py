"""系统提示构建模块，向 LLM 说明可用工具与调用格式。"""

import inspect
from typing import Callable, Dict, Any

SYSTEM_PROMPT: str = """You are a coding assistant. You have access to these tools:
- read_file(filename: str): Read file contents
- list_files(path: str): List directory contents  
- edit_file(path: str, old_str: str, new_str: str): Modify or create files

When using tools, reply with: tool: TOOL_NAME({"key": "value"})
Only output tool calls or direct responses, never both in one message.
After tool results, continue the task."""


def get_tool_str_representation(tool_name: str, registry: Dict[str, Callable[..., Dict[str, Any]]]) -> str:
    """生成单个工具的描述，供系统提示使用。"""

    tool = registry[tool_name]
    return f"{tool_name}: {tool.__doc__.split(chr(10))[0]}"


def get_full_system_prompt(registry: Dict[str, Callable[..., Dict[str, Any]]]) -> str:
    """拼接系统提示，包含所有工具描述。"""

    tool_str_repr: str = ""
    for tool_name in registry:
        tool_str_repr += "- " + get_tool_str_representation(tool_name, registry) + "\n"
    return SYSTEM_PROMPT

