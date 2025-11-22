from src.conpoments.Ast import ASTree, ASTNode
from typing import Dict, Any


class ASTBuilder:
    """AST 构建器"""

    @staticmethod
    def build_ast(script_data: Dict[str, Any], validate: bool = True) -> ASTree:
        """
        从脚本数据构建 ASTree

        Args:
            script_data: 完整的脚本数据
            validate: 是否进行验证
        """
        # 提取步骤数据
        steps_data = script_data.get('steps', {})

        # 构建AST
        ast = ASTree()
        for step_name, step_config in steps_data.items():
            # 解析actions为结构化格式
            actions = ASTBuilder._parse_actions(step_config.get('actions', {}))
            branch = step_config.get('branch', {})
            node = ASTNode(name=step_name, actions=actions, branch=branch)
            ast.add_node(node)

        # 可选验证
        if validate:
            if not ast.get_node('welcome'):
                raise ValueError("脚本必须包含 'welcome' 步骤")

        return ast

    @staticmethod
    def _parse_actions(actions_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析actions配置，返回结构化的actions字典

        Args:
            actions_config: 原始的actions配置

        Returns:
            结构化的actions字典，包含speak和listen的解析结果
        """
        parsed_actions = {}

        # 解析speak动作
        if 'speak' in actions_config:
            parsed_actions['speak'] = {
                'text': actions_config['speak'],
                'type': 'speak'
            }

        # 解析listen动作
        if 'listen' in actions_config:
            listen_str = actions_config['listen']
            if isinstance(listen_str, str):
                try:
                    # 解析 "5,20" 格式
                    parts = listen_str.split(',')
                    if len(parts) == 2:
                        timeout = int(parts[0].strip())
                        max_duration = int(parts[1].strip())
                        parsed_actions['listen'] = {
                            'timeout': timeout,
                            'max_duration': max_duration,
                            'type': 'listen'
                        }
                    else:
                        raise ValueError(f"listen格式错误，应该是'timeout,max_duration'")
                except ValueError as e:
                    raise ValueError(f"listen参数解析错误: {e}")

        return parsed_actions