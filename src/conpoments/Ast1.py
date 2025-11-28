"""
新版语法分析树（AST）模块

功能：
- ASTNode1：节点结构，包含名称、动作、分支、条件分支（if）
- ASTree1：树结构，管理所有节点，支持从json脚本构建分析树
- from_json_script：将json脚本文件转换为ASTree1对象

用法示例：
    tree = from_json_script('jd_service_script.json')
    node = tree.get_node('welcome')
    next_node = tree.get_next_node('welcome', '投诉')
"""

import json
from typing import Dict, Any, Optional, List
import os

class ASTNode1:
    """新版语法分析树节点"""
    def __init__(self, name: str, actions: Dict[str, Any], branch: Dict[str, str], ifs: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self.actions = actions
        self.branch = branch
        self.ifs = ifs or []

    def get_next_node_name(self, intention: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        根据意图和条件分支获取下一个节点名称
        :param intention: 用户意图
        :param context: 当前变量上下文（用于条件判断）
        :return: 下一个节点名称
        """
        # 优先处理条件分支
        if context and self.ifs:
            for cond in self.ifs:
                try:
                    # 简单条件表达式求值（仅支持变量替换和==, !=, >, <, >=, <=）
                    expr = cond['condition']
                    expr_eval = expr
                    for k, v in context.items():
                        expr_eval = expr_eval.replace(f"${k}", repr(v))
                    if eval(expr_eval):
                        return cond['goto']
                except Exception:
                    continue
        # 普通分支
        return self.branch.get(intention)

class ASTree1:
    """新版语法分析树容器"""
    def __init__(self):
        self.nodes: Dict[str, ASTNode1] = {}
        self.data_buffer: Dict[str, Any] = {}  # 数据缓冲区，执行时用于存储和访问用户数据
        self.input_buffer: Dict[str, Any] = {} # 输入缓冲区，存储listen内容
        self.script_name: str = ""  # 新增：脚本文件名（不带扩展名）

    def add_node(self, node: ASTNode1):
        self.nodes[node.name] = node

    def get_node(self, name: str) -> Optional[ASTNode1]:
        return self.nodes.get(name)

    def get_next_node_name(self, current_node_name: str, intention: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        根据当前节点名称和意图获取下一个节点名称
        :param current_node_name: 当前节点名称
        :param intention: 用户意图
        :param context: 当前变量上下文（用于条件判断）
        :return: 下一个节点名称
        """
        node = self.get_node(current_node_name)
        if not node:
            return None
        return node.get_next_node_name(intention, context)

def from_json_script(json_path: str) -> ASTree1:
    """
    从json脚本文件构建新版语法分析树
    :param json_path: json脚本文件路径
    :return: ASTree1对象
    """
    with open(json_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    steps = script.get("steps", {})
    tree = ASTree1()
    # 设置 script_name 为文件名（不带扩展名）
    tree.script_name = os.path.splitext(os.path.basename(json_path))[0]
    for step_name, step_cfg in steps.items():
        actions = step_cfg.get("actions", {})
        branch = step_cfg.get("branch", {})
        ifs = step_cfg.get("if", [])
        node = ASTNode1(step_name, actions, branch, ifs)
        tree.add_node(node)
    return tree

if __name__ == "__main__":
    # 测试主流程
    json_path = r"c:\Users\20232\OneDrive\大三上\程序设计与实践\大作业\项目文件\CSBotInterpreter\scripts\jd_service_script.json"
    tree = from_json_script(json_path)
    print("=== 京东客服脚本自动化测试 ===")
    # 可自定义初始上下文
    context = {
        "name": "张三",
        "is_vip": True,
        "order_id": "JD20240001",
        "status": "交易成功",
        "price": 299.0
    }
    # 运行流程，输入可用：订单、退换货、投诉、人工、意图识别失败
    tree.run("welcome", context)
    print("输入缓冲区内容：", tree.input_buffer)
