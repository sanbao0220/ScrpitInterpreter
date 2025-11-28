"""
DataAPI 数据交互组件接口说明

主要功能：
- 针对每个脚本（如京东客服）维护独立的数据目录，实现用户数据的持久化、导入、导出和管理。
- 支持与语法分析树（ASTree1）对象的数据缓冲区（data_buffer, input_buffer）进行数据同步。

核心接口：
- DataAPI(storage_dir=None): 构造函数，指定或自动定位数据存储根目录。
- import_to_tree(tree, data, merge=True): 将外部数据导入到分析树的 data_buffer。
- write_buffer_to_file(tree, filename=None, include_input=False): 将分析树缓冲区写入文件，返回文件路径。
- read_file_to_buffer(tree, filename, merge=True): 从文件读取数据并写入分析树缓冲区。
- list_files(tree=None): 列出指定脚本或所有脚本下的数据文件。
- remove_file(tree, filename): 删除指定脚本目录下的数据文件。
"""

from __future__ import annotations
import json
from typing import Any, Dict, Optional, List
from pathlib import Path


class DataAPI:
    """
    数据交互组件（每个脚本使用独立子目录）
    构造方法必须传入脚本文件名（不带扩展名），自动定位 user.data/<脚本名> 目录。
    若目录不存在则报错，存在则作为数据操作目录。
    """

    def __init__(self, script_name: str):
        # 项目根下的 user.data/<script_name>
        base = Path(__file__).resolve().parents[2] / "user.data"
        target_dir = base / script_name
        if not target_dir.exists() or not target_dir.is_dir():
            raise FileNotFoundError(f"脚本数据目录不存在: {target_dir}")
        self.storage_dir = target_dir

    def _get_script_dir(self, tree: Any = None) -> Path:
        """返回当前脚本的数据目录（已在构造时确定）"""
        return self.storage_dir

    @staticmethod
    def import_to_tree(tree: Any, data: Dict[str, Any], merge: bool = True) -> None:
        """
        将外部数据导入到分析树的 data_buffer 中
        """
        if not hasattr(tree, "data_buffer"):
            raise AttributeError("传入对象不包含 data_buffer 属性，无法导入数据。")
        if not isinstance(data, dict):
            raise TypeError("data 必须为 dict。")
        if merge:
            tree.data_buffer.update(data)
        else:
            tree.data_buffer.clear()
            tree.data_buffer.update(data)

    def write_buffer_to_file(self, tree: Any, filename: Optional[str] = None, include_input: bool = False) -> str:
        """
        只查找被修改的键，覆盖缓冲区中新的值，保持原结构和未变字段
        """
        if not hasattr(tree, "data_buffer"):
            raise AttributeError("传入对象不包含 data_buffer 属性，无法写入文件。")
        script_dir = self._get_script_dir(tree)
        if not filename:
            from datetime import datetime
            filename = f"buffer_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        safe_name = Path(filename).name
        target = script_dir / safe_name

        # 读取原内容（如有），否则新建结构
        if target.exists():
            with target.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = {}

        # 只覆盖原有字段的值，不新增字段
        old_data = payload.copy()
        new_data = dict(tree.data_buffer or {})
        for k in old_data:
            if k in new_data and old_data[k] != new_data[k]:
                payload[k] = new_data[k]
        # 如果原文件不存在，则写入所有字段
        if not old_data:
            for k, v in new_data.items():
                payload[k] = v

        with target.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return str(target.resolve())

    def read_file_to_buffer(self, tree: Any, filename: str, merge: bool = True) -> None:
        """
        从组件维护的脚本专属文件读取数据并写入分析树缓冲区
        """
        if not hasattr(tree, "data_buffer"):
            raise AttributeError("传入对象不包含 data_buffer 属性，无法读取文件。")
        script_dir = self._get_script_dir(tree)
        safe_name = Path(filename).name
        target = script_dir / safe_name
        if not target.exists():
            raise FileNotFoundError(f"文件不存在：{target}")
        with target.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        # 直接将文件内容合并到 data_buffer
        if merge:
            tree.data_buffer.update(payload)
        else:
            tree.data_buffer.clear()
            tree.data_buffer.update(payload)

    def list_files(self, tree: Any = None) -> List[str]:
        """
        列出指定脚本目录下的文件（仅文件名）。若 tree 为 None，则列出所有脚本目录下的文件（按脚本分组）。
        """
        if tree is None:
            # 列出所有脚本下的文件（带目录前缀 script_name/filename）
            out = []
            for sub in sorted(self.storage_dir.iterdir()):
                if sub.is_dir():
                    for p in sorted(sub.iterdir()):
                        if p.is_file():
                            out.append(f"{sub.name}/{p.name}")
            return out
        script_dir = self._get_script_dir(tree)
        return [p.name for p in sorted(script_dir.iterdir()) if p.is_file()]

    def remove_file(self, tree: Any, filename: str) -> bool:
        """删除指定脚本目录下的文件，返回是否成功"""
        script_dir = self._get_script_dir(tree)
        safe_name = Path(filename).name
        target = script_dir / safe_name
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False
