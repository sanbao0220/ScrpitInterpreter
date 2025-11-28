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

    def get_next_node(self, current_node_name: str, intention: str, context: Dict[str, Any] = None) -> Optional[ASTNode1]:
        node = self.get_node(current_node_name)
        if not node:
            return None
        next_name = node.get_next_node_name(intention, context)
        return self.get_node(next_name) if next_name else None

    def run(self, start_node: str, context: Dict[str, Any] = None, input_func=None, output_func=None):
        """
        从指定节点开始自动执行脚本流程
        :param start_node: 起始节点名称
        :param context: 变量上下文（如用户数据），会同步到数据缓冲区
        :param input_func: 获取用户输入的函数（可自定义，默认input）
        :param output_func: 输出函数（可自定义，默认print）
        """
        if input_func is None:
            input_func = input
        if output_func is None:
            output_func = print

        # 初始化数据缓冲区
        if context:
            self.data_buffer.update(context)
        self.input_buffer.clear()

        print(f"[DEBUG] 数据缓冲区内容: {self.data_buffer}")  # 添加调试信息

        current = self.get_node(start_node)
        while current:
            actions = current.actions
            # Speak
            if 'speak' in actions:
                text = actions['speak']
                # 修正变量替换逻辑，确保替换所有 $变量名
                for k, v in self.data_buffer.items():
                    text = text.replace(f"${{{k}}}", str(v))  # 替换 ${变量名} 为实际值
                output_func(text)  # 输出替换后的文本
            # Listen
            user_input = None
            if 'listen' in actions:
                user_input = input_func(">> ")
                self.input_buffer['listen_content'] = user_input
            # 数据更新动作（UPGRATE）
            if 'upgrate' in actions:
                for upd in actions['upgrate']:
                    val = upd['value']
                    # 修正：支持 $listen_content 变量正确赋值
                    if isinstance(val, str) and val.startswith("$"):
                        var_name = val[1:]
                        if var_name == "listen_content":
                            val = self.input_buffer.get("listen_content", "")
                        else:
                            val = self.data_buffer.get(var_name, val)
                    self.data_buffer[upd['field']] = val
            # Middle 动作处理
            if actions.get('middle', False):
                # 跳转到middleProc节点
                middle_node = self.get_node('middleProc')
                if middle_node:
                    current = middle_node
                    continue
                else:
                    raise RuntimeError("未找到 middleProc 节点，无法执行 Middle 动作")
            # Exit 动作处理
            if actions.get('exit', False):
                # 跳转到exit节点并退出
                exit_node = self.get_node('exit')
                if exit_node:
                    actions = exit_node.actions
                    if 'speak' in actions:
                        output_func(actions['speak'])
                break
            # 条件分支
            next_node_name = None
            if current.ifs and self.data_buffer:
                for cond in current.ifs:
                    expr = cond['condition']
                    expr_eval = expr
                    for k, v in self.data_buffer.items():
                        expr_eval = expr_eval.replace(f"${k}", repr(v))
                    try:
                        if eval(expr_eval):
                            next_node_name = cond['goto']
                            break
                    except Exception:
                        continue
            # 普通分支
            if not next_node_name:
                if user_input and user_input in current.branch:
                    next_node_name = current.branch[user_input]
                elif '意图识别失败' in current.branch:
                    next_node_name = current.branch['意图识别失败']
                elif '结束' in current.branch:
                    next_node_name = current.branch['结束']
                else:
                    next_node_name = None
            if not next_node_name:
                break
            current = self.get_node(next_node_name)

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
