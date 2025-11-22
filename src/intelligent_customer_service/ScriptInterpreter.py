from abc import ABC
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from src.conpoments.Ast import ASTNode, ASTree
from src.conpoments.ASTBuilder import ASTBuilder
from src.conpoments.get_jsonScript import text_script_to_json_file  # 修改导入

# === 上下文类 ===
class Context:
    """执行上下文"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.current_node: Optional[ASTNode] = None
        self.execution_history: List[str] = []
        self.intention: Optional[str] = None  # 当前识别到的意图（可由外部或 LLM 填充）


# === 脚本解释器基类 ===
class ScriptInterpreter(ABC):
    """脚本解释器基类（最后定义，避免循环引用）"""

    def __init__(self, script_path: Path):
        """初始化脚本，加载 JSON 并构建语法树"""
        self._ast: Optional[ASTree] = None
        self.metadata = {'script_type': self.__class__.__name__}
        self._script_data: Dict[str, Any] = {}
        self.intention = '沉默'  # 默认意图名称（与脚本中的 branch key 对应）

        try:
            if script_path.suffix == ".json":
                with open(script_path, 'r', encoding='utf-8') as f:
                    self._script_data = json.load(f)
            elif script_path.suffix == ".txt":
                # 先生成 JSON 文件，再读取
                json_path = text_script_to_json_file(script_path.name, script_path.parent.as_posix())
                with open(json_path, 'r', encoding='utf-8') as f:
                    self._script_data = json.load(f)
            else:
                raise RuntimeError("仅支持 .json 或 .txt 脚本文件")
            self.metadata.update(self._script_data.get('metadata', {}))
            self._ast = ASTBuilder.build_ast(self._script_data)
            self._log(f"脚本加载成功: {script_path}")
        except Exception as e:
            raise RuntimeError(f"脚本初始化失败: {e}")

    def execute(self, context: Context) -> Dict[str, Any]:
        """驱动语法树执行"""
        if not self._ast:
            raise RuntimeError("未构建语法树")

        # 从 welcome 开始
        current = self._ast.get_node('welcome')
        context.current_node = current
        results = {}

        while current:
            #三个步骤完成一个step
            # 1. 将动作执行视为节点方法
            current.perform_actions(context, self._log)
            # 2. 调用意图分析接口

            # 记录变量快照和历史
            results[current.name] = context.variables.copy()
            context.execution_history.append(current.name)

            #3.  决策下一个节点名：优先使用 context.intention，否则使用脚本默认 self.intention
            use_intent = context.intention if context.intention is not None else self.intention
            next_node = self._ast.get_next_node(current.name, use_intent)

            # 更新当前节点
            context.current_node = next_node
            current = next_node

        return results


    def _log(self, message: str):
        """内置日志"""
        print(f"[{self.metadata['script_type']}] {message}")

