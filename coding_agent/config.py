"""配置加载与工作目录解析模块。
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

from coding_agent.models import LLMConfig

load_dotenv()


def resolve_workdir(workdir: Optional[str]) -> Path:
    """解析工作目录，支持命令行参数或环境变量 AGENT_WORKDIR。

    参数：
        workdir: 命令行传入的目录字符串，可为空

    返回：
        Path: 作为文件操作根目录的绝对路径

    关键检查：
        - 若 workdir 为空，优先读取环境变量 AGENT_WORKDIR，否则取当前工作目录
        - 路径必须存在且为目录，否则抛出 ValueError
    """

    candidate = workdir or os.environ.get("AGENT_WORKDIR")
    base_path: Path = Path(candidate) if candidate else Path.cwd()
    resolved = base_path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"工作目录不存在: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"工作目录不是文件夹: {resolved}")
    return resolved


def build_provider_config(provider: str) -> LLMConfig:
    """根据提供者名称创建配置，确保密钥和路由完整。

    参数：
        provider: LLM 提供者名称（'glm4.7' 或 'deepseek'）

    返回：
        LLMConfig: 完整的 LLM 连接配置对象

    异常：
        ValueError: 若提供者不被支持
        EnvironmentError: 若对应的环境变量缺失或为空
    """

    provider_lower: str = provider.lower()
    provider_table: Dict[str, Dict[str, str]] = {
        "glm4.7": {
            "env": "GLM_API_KEY",
            "model": "glm-4-7",
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        },
        "deepseek": {
            "env": "DEEPSEEK_API_KEY",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
        },
    }
    if provider_lower not in provider_table:
        raise ValueError(f"不支持的提供者: {provider_lower}")

    env_name: str = provider_table[provider_lower]["env"]
    api_key: Optional[str] = os.environ.get(env_name)
    if api_key is None or api_key == "":
        raise EnvironmentError(f"缺少必要环境变量 {env_name}")

    return LLMConfig(
        provider=provider_lower,
        api_key=api_key,
        model=provider_table[provider_lower]["model"],
        base_url=provider_table[provider_lower]["base_url"],
        temperature=0.2,
        max_tokens=600,
    )
