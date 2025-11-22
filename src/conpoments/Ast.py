"""
语法分析树（AST）模块

本模块实现了一个简单的语法分析树结构，用于管理对话流程中的节点和跳转逻辑。
采用数据类与逻辑分离的设计，ASTNode为纯数据结构，ASTree为容器管理类。

主要功能：
1. 定义对话节点结构，包含节点名称、执行动作和分支跳转逻辑
2. 管理节点集合，支持节点的添加、查询和更新
3. 根据当前节点和用户意图确定下一个对话节点

核心类说明：
- ASTNode: 语法分析树节点，存储节点配置和跳转逻辑
- ASTree: 语法分析树容器，管理所有节点并提供导航功能

API说明：
ASTNode类：
- get_next_node_name(intention): 根据意图获取下一个节点名称
- perform_actions(context, logger): 执行节点动作（当前为空实现）

ASTree类：
- add_node(node): 添加节点到语法树
- get_node(name): 按名称获取节点
- difine_node(node): 定义或更新节点（add_node的别名）
- get_next_node(current_node_name, intention): 根据当前节点和意图获取下一个节点

使用示例：
    tree = ASTree()
    node = ASTNode("welcome", ["action1", "action2"], {"投诉": "complainProc"})
    tree.add_node(node)
    next_node = tree.get_next_node("welcome", "投诉")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable

@dataclass
class ASTNode:
    """语法分析树节点（纯数据结构）"""
    name: str  # 节点名称（如"welcome"）
    actions: Any  # 原始actions配置（可能是列表或字符串等，保持兼容）
    branch: Dict[str, str]  # 意图->目标节点映射（如{"投诉":"complainProc"})

    def get_next_node_name(self, intention: str) -> Optional[str]:
        """根据意图获取下一个节点名称"""
        return self.branch.get(intention)

    def perform_actions(self, context: Any, logger: Optional[Callable[[str], None]] = None) -> None:
       return



class ASTree:
    """语法分析树容器（与脚本类完全解耦）"""

    def __init__(self):
        self.nodes: Dict[str, ASTNode] = {}  # 节点名称->节点对象映射

    def add_node(self, node: ASTNode):
        """添加节点到语法树"""
        self.nodes[node.name] = node

    def get_node(self, name: str) -> Optional[ASTNode]:
        """按名称获取节点"""
        return self.nodes.get(name)

    def difine_node(self, node: ASTNode):
        """定义或更新节点"""
        self.nodes[node.name] = node

    def get_next_node(self, current_node_name: str, intention: str) -> Optional[ASTNode]:
        """
        获取下一个节点对象
        :param current_node_name: 当前节点名称
        :param intention: 当前意图
        :return: 下一个节点对象（若存在）
        """
        current_node = self.nodes.get(current_node_name)
        if not current_node:
            return None

        next_node_name = current_node.get_next_node_name(intention)
        return self.nodes.get(next_node_name) if next_node_name else None