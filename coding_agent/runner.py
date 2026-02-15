"""交互循环与工具执行闭环逻辑。"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from coding_agent.llm_client import build_llm_client, execute_llm_call
from coding_agent.models import LLMConfig, ToolInvocation
from coding_agent.prompt import get_full_system_prompt
from coding_agent.tools import Toolset

YOU_COLOR: str = "\u001b[94m"
ASSISTANT_COLOR: str = "\u001b[93m"
RESET_COLOR: str = "\u001b[0m"


def extract_tool_invocations(text: str) -> List[ToolInvocation]:
    """解析 LLM 返回中的工具调用行，返回结构化调用信息。"""

    invocations: List[ToolInvocation] = []
    for raw_line in text.splitlines():
        line: str = raw_line.strip()
        if not line.startswith("tool:"):
            continue
        after: str = line[len("tool:"):].strip()
        if "(" not in after or not after.endswith(")"):
            continue
        name, rest = after.split("(", 1)
        args_json: str = rest[:-1].strip()
        args: Dict[str, Any] = json.loads(args_json)
        invocations.append(ToolInvocation(tool_name=name.strip(), args=args))
    return invocations


def run_coding_agent_loop(config: LLMConfig, workdir: Path) -> None:
    """启动交互循环，按阶段执行用户交互、LLM 调用与工具落地。"""

    # 第一阶段：准备系统上下文与 LLM 客户端。
    toolset = Toolset(workdir)
    registry = toolset.registry()
    system_prompt: str = get_full_system_prompt(registry)
    conversation: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    client = build_llm_client(config)
    max_history_turns: int = 10
    print(system_prompt)

    # 第二阶段：循环接收用户输入，并驱动工具调用闭环。
    while True:
        try:
            user_input: str = input(f"{YOU_COLOR}You:{RESET_COLOR}:")
        except (KeyboardInterrupt, EOFError):
            break
        conversation.append({"role": "user", "content": user_input.strip()})

        # 第三阶段：LLM 推理与工具执行闭环。
        while True:
            # 滑动窗口：保留系统提示 + 最近 N 轮对话，防止 context 溢出
            windowed_conversation: List[Dict[str, str]] = [conversation[0]]
            windowed_conversation.extend(conversation[max(1, len(conversation) - 2 * max_history_turns):])
            assistant_response: str = execute_llm_call(windowed_conversation, client, config)
            invocations: List[ToolInvocation] = extract_tool_invocations(assistant_response)
            if len(invocations) == 0:
                print(f"{ASSISTANT_COLOR}Assistant:{RESET_COLOR}: {assistant_response}")
                conversation.append({"role": "assistant", "content": assistant_response})
                break

            for invocation in invocations:
                tool: Callable[..., Dict[str, Any]] = registry[invocation.tool_name]
                args: Dict[str, Any] = invocation.args
                result: Dict[str, Any]

                try:
                    if invocation.tool_name == "read_file":
                        if "filename" not in args:
                            raise ValueError("read_file 缺少 filename 参数")
                        result = tool(args["filename"])
                    elif invocation.tool_name == "list_files":
                        if "path" not in args:
                            raise ValueError("list_files 缺少 path 参数")
                        result = tool(args["path"])
                    elif invocation.tool_name == "edit_file":
                        missing_keys: List[str] = [key for key in ["path", "old_str", "new_str"] if key not in args]
                        if len(missing_keys) > 0:
                            raise ValueError(f"edit_file 缺少参数: {missing_keys}")
                        result = tool(args["path"], args["old_str"], args["new_str"])
                    else:
                        raise ValueError(f"未知工具: {invocation.tool_name}")
                except ValueError as tool_error:
                    error_payload: Dict[str, Any] = {
                        "success": False,
                        "error": str(tool_error),
                        "tool": invocation.tool_name,
                        "args": args,
                    }
                    conversation.append({"role": "user", "content": f"tool_result({json.dumps(error_payload)})"})
                    print(f"{ASSISTANT_COLOR}Assistant:{RESET_COLOR}: {tool_error}")
                    break

                conversation.append({"role": "user", "content": f"tool_result({json.dumps(result)})"})
