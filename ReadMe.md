# Coding Agent 编码助手

一个功能完整的本地编码代理，可以自主读取、列表和修改工作目录下的文件，支持 GLM4.7 与 DeepSeek 两个 LLM 提供者。系统在启动时自动暴露所有工具能力给模型，模型可以通过自然语言指令自主调用工具完成代码编辑、文件查看等任务。整个系统遵循严格的研究型代码规范，所有函数包含完整的类型注解与中文文档，运行时无默认值，错误处理透明可追踪。

## 快速开始

### 环境准备

确保 Python 3.10 及以上版本，安装依赖：

```bash
pip install openai python-dotenv
```

在项目根目录创建 `.env` 文件，填入 API 密钥与可选工作目录：

```bash
AGENT_PROVIDER=glm4.7          # glm4.7 或 deepseek
GLM_API_KEY=你的GLM密钥          # 选择 glm4.7 时必填
DEEPSEEK_API_KEY=你的DeepSeek密钥  # 选择 deepseek 时必填
AGENT_WORKDIR=/path/to/workdir # 可选，文件操作的根目录
```

环境变量也可在终端直接导出。缺失时程序会立即报错而不使用默认值；工作目录未指定时默认当前目录。

### 运行

```bash
python coding_agent_from_scratch_lecture.py
```

可选参数：

- `--provider glm4.7|deepseek`：显式选择提供者（默认读取环境变量 AGENT_PROVIDER）
- `--workdir /path/to/dir`：指定文件操作根目录（默认读取 AGENT_WORKDIR 或当前目录）

示例：

```bash
python coding_agent_from_scratch_lecture.py --provider deepseek --workdir .
```

终端会打印系统提示及可用工具列表，随后可输入自然语言需求，模型自动执行文件操作并返回结果。

## 构造原理

### 代码结构

- coding_agent_from_scratch_lecture.py：入口脚本，委托至模块化实现
- coding_agent/cli.py：命令行解析，处理 provider/workdir 选择
- coding_agent/config.py：环境变量与提供者配置解析
- coding_agent/tools.py：文件读/列/写工具，受工作目录限制
- coding_agent/prompt.py：系统提示拼装与工具描述
- coding_agent/llm_client.py：LLM 客户端与调用封装
- coding_agent/runner.py：主交互循环与工具调用闭环
- coding_agent/models.py：LLMConfig、ToolInvocation 数据结构

### 整体架构

系统采用"收集→推理→执行"的三阶段循环架构：

**第一阶段：初始化**。系统读取环境变量获取 LLM 密钥，构建 OpenAI 兼容客户端。系统提示中动态嵌入三个工具的完整函数签名与文档，确保模型清楚能力边界。

**第二阶段：用户交互**。循环接收用户输入，追加到对话历史。Ctrl+C 或 EOF 时优雅退出。

**第三阶段：LLM 推理与工具执行闭环**。向 LLM 发送对话历史，检查返回文本中是否包含工具调用行（格式为 `tool: TOOL_NAME({...})`）。若无工具调用则输出回复并返回第二阶段；若有则逐个执行工具，将结果（包含诊断信息）追加到对话历史，重复第三阶段直到模型无需更多工具调用。

### 核心模块

**工具模块**：三个核心工具函数实现文件操作。`read_file_tool` 读取文件内容；`list_files_tool` 列出目录结构；`edit_file_tool` 创建或替换文件内容。所有工具都返回完整的诊断信息（字节长度、行数、操作类型、成功标记），便于问题排查。

**配置管理**：`LLMConfig` 数据类保存 API 密钥、模型名、基址等连接参数。`build_provider_config` 根据环境变量构建配置，运行时验证密钥存在且非空，没有默认值，避免逻辑错误。

**调用解析**：`extract_tool_invocations` 逐行解析 LLM 返回，提取工具名与 JSON 参数，支持单行或多行工具调用。格式验证严格，不合法行自动跳过。

**对话管理**：使用列表维护完整对话历史，按 OpenAI API 格式（role/content）存储。LLM 推理结果和工具执行结果都追加到历史，便于多轮对话和问题排查。

### 工具调用流程

1. LLM 返回文本，系统逐行扫描查找 `tool:` 前缀
2. 提取工具名和 JSON 参数，校验参数完整性
3. 查询 `TOOL_REGISTRY` 获取对应函数指针
4. 执行工具，获得包含诊断信息的结果字典
5. 将 `tool_result(...)` 追加到对话历史
6. 继续推理直到模型无需更多调用

## 使用示例

### 查看文件

输入：`请查看 coding_agent_from_scratch_lecture.py 的前50行`

模型会调用 `read_file_tool` 读取文件，再根据内容自动截取或总结相关部分。

### 修改文件

输入：`把 ReadMe.md 中的"快速开始"改成"Get Started"`

模型会先读取文件，定位到相关行，调用 `edit_file_tool` 替换内容，返回修改诊断。

### 创建新文件

输入：`创建一个名为 test.py 的文件，内容是一个 hello world 程序`

模型调用 `edit_file_tool` 且参数 `old_str=""` 以创建新文件。

### 列出目录

输入：`列出当前目录的所有文件和子目录`

模型调用 `list_files_tool` 返回项目结构。

## 代码规范

遵循 AGENTS.md 中的研究型代码开发规范：

**类型注解**：所有函数签名包含完整类型注解（参数和返回值），使用 `Union`、`Dict`、`List` 等处理复杂类型。

**中文文档**：每个模块、类、函数都包含详细 docstring，说明功能、参数、返回值、异常和关键实现细节。系统提示中也包含工具文档供 LLM 参考。

**阶段化注释**：复杂逻辑使用"第一阶段""第二阶段"等注释分组，快速定位代码意图。

**依赖管理**：按标准库→第三方库→项目内部的顺序导入，每个模块只导入必需依赖。

**命名规范**：类名 PascalCase，变量使用描述性名称。未使用但需保留的变量前缀下划线。

**错误处理**：关键操作（密钥检查、文件访问、参数验证）都有明确的异常抛出，不使用 try-except 掩盖问题，便于问题追踪。

## 扩展方向

### 添加新工具

按现有模式编写新工具函数，签名遵循类型注解规范，返回值包含诊断信息。将函数注册到 `TOOL_REGISTRY` 字典，系统提示会自动暴露。

示例：添加 Shell 执行工具

```python
def execute_shell_tool(command: str) -> Dict[str, Any]:
    """执行 Shell 命令并返回输出。
    
    参数：
        command: 要执行的 Shell 命令
        
    返回：
        包含 stdout、stderr、return_code、success 的诊断字典
    """
    # 实现命令执行逻辑
    pass

TOOL_REGISTRY["execute_shell"] = execute_shell_tool
```

### 持久化对话

当前对话存在内存中，会话结束即丢失。可以添加对话保存/加载功能，支持恢复长期对话上下文。

### 提示词优化

当前系统提示简洁直接。可以根据使用场景优化提示词，例如添加"优先安全性""避免破坏性操作"等指导。

### 多文件编辑

当前 `edit_file_tool` 支持单文件单次替换。可以扩展支持批量替换、正则表达式匹配等高级特性。

## 故障排查

**缺少环境变量**：检查 `.env` 是否加载或终端导出了密钥。程序不使用默认值，缺失会立即报 `EnvironmentError`。

**模型无法调用工具**：确认输入没有被截断（LLM context 限制），或调整 `SYSTEM_PROMPT` 增强工具暴露。

**文件操作失败**：查看返回结果中的 `diagnostics` 字段。若 `action='old_str_not_found'`，说明替换文本不在文件中；若 `success=False`，查看错误信息。

**路径问题**：所有路径都自动转换为绝对路径。若出现权限或不存在错误，检查是否有文件系统权限或路径是否正确。

## 依赖清单

- `openai>=1.0.0`：OpenAI API 客户端，支持兼容接口
- `python-dotenv`：环境变量管理
- `pathlib`（标准库）：路径处理
- `dataclasses`（标准库）：数据类定义
- `json`（标准库）：JSON 解析
- `typing`（标准库）：类型注解

## 许可

遵循 AGENTS.md 规范，所有提交必须仅显示人类开发者作为唯一作者，禁止 AI 贡献者标识。
