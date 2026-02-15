"""命令行入口，支持选择提供者与工作目录。"""

import argparse
import os
from typing import Optional

from coding_agent.config import build_provider_config, resolve_workdir
from coding_agent.runner import run_coding_agent_loop


def main(argv: Optional[list[str]] = None) -> None:
    """启动编码代理。

    支持通过 --provider 指定 LLM 提供者，通过 --workdir 指定工作根目录。
    若未指定 provider，则读取环境变量 AGENT_PROVIDER。
    """

    parser = argparse.ArgumentParser(description="Coding Agent CLI")
    parser.add_argument("--provider", type=str, help="LLM provider: glm4.7 or deepseek", default=None)
    parser.add_argument("--workdir", type=str, help="工作目录根路径", default=None)
    args = parser.parse_args(argv)

    provider = args.provider or os.environ.get("AGENT_PROVIDER")
    if provider is None or provider == "":
        raise EnvironmentError("请通过 --provider 或环境变量 AGENT_PROVIDER 指定 LLM 提供者 (glm4.7 或 deepseek)")

    workdir = resolve_workdir(args.workdir)
    config = build_provider_config(provider)
    run_coding_agent_loop(config, workdir)


if __name__ == "__main__":
    main()
