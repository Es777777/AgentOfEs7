"""工具集合，实现文件读取、列出与编辑操作。
"""

from pathlib import Path
from typing import Any, Callable, Dict, List


class Toolset:
    """文件操作工具集合，限定在给定工作目录内执行。

    属性：
        workdir: 工作目录根路径，所有操作均以此为基准
    """

    def __init__(self, workdir: Path) -> None:
        self.workdir: Path = workdir

    def _resolve_abs_path(self, path_str: str) -> Path:
        """将传入路径解析为工作目录内的绝对路径。

        若解析后路径不在工作目录下，则抛出 ValueError 以避免越权访问。
        """

        candidate = Path(path_str).expanduser()
        target = (self.workdir / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        try:
            target.relative_to(self.workdir)
        except ValueError as exc:
            raise ValueError(f"路径越界，禁止访问工作目录以外的文件: {target}") from exc
        return target

    def read_file(self, filename: str) -> Dict[str, Any]:
        """读取指定文件的完整内容并返回诊断信息。

        参数：
            filename: 文件路径（相对工作目录或绝对路径）
        """

        full_path = self._resolve_abs_path(filename)
        content: str = full_path.read_text(encoding="utf-8")
        diagnostics: Dict[str, Any] = {
            "byte_length": len(content.encode("utf-8")),
            "line_count": len(content.splitlines()),
        }
        return {
            "file_path": str(full_path),
            "content": content,
            "success": True,
            "diagnostics": diagnostics,
        }

    def list_files(self, path: str) -> Dict[str, Any]:
        """列出目录内容（子目录和文件）。

        参数：
            path: 要列出的目录路径（相对工作目录或绝对路径）
        """

        full_path = self._resolve_abs_path(path)
        files: List[Dict[str, str]] = []
        for item in full_path.iterdir():
            files.append({"filename": item.name, "type": "file" if item.is_file() else "dir"})
        diagnostics: Dict[str, Any] = {"count": len(files), "path": str(full_path)}
        return {
            "path": str(full_path),
            "files": files,
            "success": True,
            "diagnostics": diagnostics,
        }

    def edit_file(self, path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """创建新文件或替换现有文件内容。若 old_str 为空则创建新文件。

        参数：
            path: 目标文件路径
            old_str: 待替换的原文本，空串时表示创建文件
            new_str: 新文本内容
        """

        full_path = self._resolve_abs_path(path)
        if old_str == "":
            full_path.write_text(new_str, encoding="utf-8")
            diagnostics = {"action": "created_file", "byte_length": len(new_str.encode("utf-8"))}
            return {"path": str(full_path), "success": True, "diagnostics": diagnostics}

        original = full_path.read_text(encoding="utf-8")
        if old_str not in original:
            diagnostics = {"action": "old_str_not_found", "needle": old_str}
            return {"path": str(full_path), "success": False, "diagnostics": diagnostics}

        edited = original.replace(old_str, new_str, 1)
        full_path.write_text(edited, encoding="utf-8")
        diagnostics = {
            "action": "edited",
            "original_length": len(original),
            "edited_length": len(edited),
        }
        return {"path": str(full_path), "success": True, "diagnostics": diagnostics}

    def registry(self) -> Dict[str, Callable[..., Dict[str, Any]]]:
        """返回工具注册表，键为工具名，值为可调用对象。"""

        return {
            "read_file": self.read_file,
            "list_files": self.list_files,
            "edit_file": self.edit_file,
        }
