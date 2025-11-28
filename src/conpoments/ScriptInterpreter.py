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

class ScriptInterpreter:
    def __init__(self, script_path: Path):
        # 始终传入文本脚本文件，自动转换为JSON并构建语法分析树
        if script_path.suffix == ".txt":
            json_path = text_script_to_json_file(script_path.name, script_path.parent.as_posix())
            self.tree = from_json_script(json_path)
        else:
            raise RuntimeError("仅支持 .txt 脚本文件")
        self.api = DataAPI(self.tree.script_name)

    def load_user_data(self, user_file: str):
        # 从 user.data/<script_name>/<user_file> 加载用户数据到缓冲区
        self.current_user_file = user_file
        try:
            self.api.read_file_to_buffer(self.tree, user_file, merge=True)
        except Exception as e:
            print(f"[ERROR] 加载用户数据文件失败: {e}")  # 捕获并打印异常

    def run(self):
        # 执行脚本流程
        print(f"【脚本：{self.tree.script_name}】智能客服对话开始")
        self.tree.run("welcome", self.tree.data_buffer)
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
