"""
ScriptInterpreter 智能客服脚本分析器

运行说明：
- 请在项目根目录下运行本文件，或确保PYTHONPATH包含项目根目录。
- 推荐命令：python -m src.intelligent_customer_service.ScriptInterpreter

功能说明：
- 支持从文本脚本或JSON脚本加载业务流程，自动构建语法分析树（ASTree1）
- 支持用户数据缓冲区、输入缓冲区，自动与DataAPI进行数据读写
- 支持脚本自动执行，流程控制、分支跳转、数据更新
- 支持命令行交互测试

核心接口：
- ScriptInterpreter(script_path: Path): 构造方法，加载脚本并构建分析树
- load_user_data(user_file: str): 加载指定用户数据到分析树
- run(): 执行脚本流程，自动处理分支和数据
- save_user_data(filename: str = None): 保存当前缓冲区数据到文件
"""

from pathlib import Path
from get_jsonScript import text_script_to_json_file
from Ast1 import ASTree1, from_json_script
from data_api import DataAPI
from modelAPI import client, extract_branches, recognize_intent  # 引入大模型调用的客户端和辅助函数

class ScriptInterpreter:
    def __init__(self, script_path: Path):
        # 始终传入文本脚本文件，自动转换为JSON并构建语法分析树
        if script_path.suffix == ".txt":
            json_path = text_script_to_json_file(script_path.name, script_path.parent.as_posix())
            self.tree = from_json_script(json_path)
        else:
            raise RuntimeError("仅支持 .txt 脚本文件")
        self.api = DataAPI(self.tree.script_name)
        self.llm_client = client  # 初始化大模型客户端

        # 初始化可能的意图列表
        self.possible_intents = extract_branches(script_path)
        print(f"[INFO] 提取的可能意图: {self.possible_intents}")

    def load_user_data(self, user_file: str):
        # 从 user.data/<script_name>/<user_file> 加载用户数据到缓冲区
        self.current_user_file = user_file
        try:
            self.api.read_file_to_buffer(self.tree, user_file, merge=True)
        except Exception as e:
            print(f"[ERROR] 加载用户数据文件失败: {e}")  # 捕获并打印异常

    def recognize_intent(self, user_input: str) -> str:
        """
        调用大模型 API 识别用户意图。
        :param user_input: 用户的自然语言输入
        :return: 识别出的意图（如 "投诉", "账单", "意图识别失败" 等）
        """
        try:
            intent = recognize_intent(user_input, self.possible_intents)
            return intent
        except Exception as e:
            print(f"[ERROR] 意图识别失败: {e}")
            return "意图识别失败"

    def run(self):
        """
        执行脚本流程
        """
        print(f"【脚本：{self.tree.script_name}】智能客服对话开始")
        current_step = "welcome"
        while current_step:
            # 获取下一个节点
            next_step = None
            print(f"[DEBUG] 当前步骤: {current_step}")
            current_node = self.tree.get_node(current_step)
            if not current_node:
                print(f"[ERROR] 未找到步骤: {current_step}")
                break

            # 遍历动作列表，按顺序执行
            for action in current_node.actions:
                action_type = action.get("type")
                if action_type == "speak":
                    # 执行 Speak 动作
                    text = action.get("content", "")
                    for k, v in self.tree.data_buffer.items():
                        text = text.replace(f"${{{k}}}", str(v))
                    print(text)

                elif action_type == "listen":
                    # 执行 Listen 动作
                    min_time = action.get("min", 0)
                    max_time = action.get("max", 0)
                    print(f"[INFO] 监听用户输入，最短时间: {min_time}s, 最长时间: {max_time}s")
                    user_input = input(">> ")
                    self.tree.input_buffer['listen_content'] = user_input

                    # 调用大模型进行意图识别
                    intent = self.recognize_intent(user_input)
                    print(f"[INFO] 用户意图识别结果: {intent}")
                    self.tree.input_buffer['intent'] = intent

                elif action_type == "upgrate":
                    # 执行数据更新动作（UPGRATE）
                    field = action.get("field")
                    value = action.get("value")
                    if isinstance(value, str) and value.startswith("$"):
                        var_name = value[1:]
                        if var_name == "listen_content":
                            value = self.tree.input_buffer.get("listen_content", "")
                        else:
                            value = self.tree.data_buffer.get(var_name, value)
                    if self.tree.data_buffer.get(field) != value:
                        self.tree.data_buffer[field] = value
                        print(f"[INFO] 数据更新: {field} -> {value}")
                        # 立即写回文件
                        self.api.write_buffer_to_file(self.tree, filename=self.current_user_file)

                elif action_type == "middle":
                    # 处理 Middle 动作
                    print(f"[DEBUG] Middle 动作触发，跳转到 middleProc")
                    next_step = "middleProc"
                    break

                elif action_type == "exit":
                    # 处理 Exit 动作
                    print("对话结束")
                    return


            
            intent = self.tree.input_buffer.get("intent")
            # 优先使用 branch 分支进行跳转
            if next_step == None:
                if intent and intent in current_node.branch:
                    next_step = current_node.branch[intent]
                    print(f"[DEBUG] 根据分支意图跳转到: {next_step}")
                elif intent:
                    next_step = self.tree.get_next_node_name(current_step, intent, self.tree.data_buffer)
                    print(f"[DEBUG] 根据条件分支跳转到: {next_step}")
                if not next_step and "意图识别失败" in current_node.branch:
                    print(f"[DEBUG] 意图识别失败，跳转到 fail")
                    next_step = current_node.branch["意图识别失败"]
                if not next_step:
                    print(f"[WARN] 无法确定下一步，结束对话")
                    break

            current_step = next_step

        # 执行完自动保存数据到当前用户文件
        self.save_user_data(self.current_user_file)

    def save_user_data(self, filename: str = None):
        # 使用DataAPI接口，合并写回用户数据文件
        target_file = filename if filename else getattr(self, "current_user_file", None)
        if not target_file:
            raise ValueError("未指定用户数据文件名")
        # 先读取原数据到缓冲区（merge=True），再写回
        self.api.read_file_to_buffer(self.tree, target_file, merge=True)
        path = self.api.write_buffer_to_file(self.tree, filename=target_file, include_input=True)
    

if __name__ == "__main__":
    # 示例：组装并运行京东客服脚本
    script_path = Path(__file__).resolve().parents[2] / "scripts/jd_service_script.txt"
    interpreter = ScriptInterpreter(script_path)
    user_data_path = Path(__file__).resolve().parents[2] / "user.data/jd_service_script/user_zhangsan.json"
    interpreter.load_user_data(user_data_path.as_posix())
    interpreter.run()
