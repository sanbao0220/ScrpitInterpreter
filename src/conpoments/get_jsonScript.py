import re
import json
import os

"""
核心调用方法:
-----------------
text_script_to_json_file(filename, scripts_dir=None) -> str
   - 读取指定目录下的文本脚本文件，转换为 JSON 文件并返回 JSON 文件路径（始终覆盖写入）。
   - 用法示例：
       from get_jsonScript import text_script_to_json_file
       json_path = text_script_to_json_file('text_script.txt')
       print(json_path)

辅助函数列表:
-----------------
- parse_text_script(text_script: str, metadata=None) -> dict
    解析文本脚本字符串为 JSON 脚本字典。
- _expr_to_template(expr: str) -> str
    将 $var + "文本" + $var2 形式的表达式转换为 "${var}文本${var2}" 模板字符串。

"""

def _expr_to_template(expr: str) -> str:
    """
    将 $var + "文本" + $var2 形式的表达式转换为 "${var}文本${var2}" 模板字符串
    """
    expr = expr.strip()
    parts = re.findall(r'(\$[a-zA-Z_][\w]*)|"(.*?)"', expr)
    result = ""
    for var, txt in parts:
        if var:
            result += f"${{{var[1:]}}}"
        else:
            result += txt
    return result

def parse_text_script(text_script: str, metadata=None):
    """
    解析文本脚本为JSON脚本格式，支持UPGRATE、If条件分支等
    :param text_script: 文本脚本字符串
    :param metadata: 可选，元数据字典
    :return: JSON脚本字典
    """
    steps = {}
    current_step = None
    actions = []
    branch = {}
    ifs = []

    def flush_step():
        nonlocal current_step, actions, branch, ifs
        if current_step:
            step_dict = {
                "name": current_step,
                "actions": actions.copy(),
                "branch": branch.copy()
            }
            if ifs:
                step_dict["if"] = ifs.copy()
            steps[current_step] = step_dict
        actions = []
        branch = {}
        ifs = []

    lines = text_script.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        m = re.match(r"Step\s+(\w+)", line)
        if m:
            flush_step()
            current_step = m.group(1)
            continue
        m = re.match(r"Speak\s+(.+)", line)
        if m:
            speak_expr = m.group(1).strip()
            if '+' in speak_expr or '$' in speak_expr:
                speak_content = _expr_to_template(speak_expr)
            else:
                speak_content = speak_expr.strip('"')
            actions.append({"type": "speak", "content": speak_content})
            continue
        m = re.match(r"Listen\s+([\d]+)\s*,\s*([\d]+)", line)
        if m:
            actions.append({"type": "listen", "min": int(m.group(1)), "max": int(m.group(2))})
            continue
        m = re.match(r"UPGRATE\s+\$([a-zA-Z_][\w]*)\s+\"?([^\"]*)\"?", line)
        if m:
            actions.append({"type": "upgrate", "field": m.group(1), "value": m.group(2)})
            continue
        m = re.match(r"If\s+(.+?)\s+Then\s+(\w+)", line)
        if m:
            cond = m.group(1).strip().replace('"', "'")
            ifs.append({"condition": cond, "goto": m.group(2)})
            continue
        # 支持 Branch "结束", exit 或 Branch 结束, exit
        m = re.match(r'Branch\s+"(.+?)"\s*,\s*(\w+)', line)
        if m:
            branch_key = m.group(1)
            branch_val = m.group(2)
            branch[branch_key] = branch_val
            continue
        m = re.match(r'Branch\s+(.+?),\s*(\w+)', line)
        if m:
            branch_key = m.group(1)
            branch_val = m.group(2)
            branch[branch_key] = branch_val
            continue
        # 将Exit作为动作
        if re.match(r"Exit", line):
            actions.append({"type": "exit"})
            continue
        # 将Middle作为动作
        if re.match(r"Middle", line):
            actions.append({"type": "middle"})
            continue

    flush_step()

    json_script = {
        "metadata": metadata or {
            "name": "自动生成脚本",
            "version": "1.0",
            "description": "由文本脚本自动转换"
        },
        "steps": steps
    }
    return json_script

def text_script_to_json_file(filename: str, scripts_dir: str = None) -> str:
    """
    将指定 scripts 目录下的文本脚本文件转换为 JSON 文件，并返回 JSON 文件路径。
    如果 JSON 文件已存在，则覆盖为最新内容。
    :param filename: 文本脚本文件名（如 text_script.txt）
    :param scripts_dir: 脚本目录（默认与本文件同级的 ../../scripts）
    :return: 生成的 JSON 文件路径
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir is None:
        scripts_dir = os.path.join(base_dir, "..", "..", "scripts")
    if os.path.isabs(filename):
        script_path = filename
        scripts_dir = os.path.dirname(filename)
    else:
        script_path = os.path.join(scripts_dir, filename)
    json_filename = os.path.splitext(os.path.basename(filename))[0] + ".json"
    json_output_path = os.path.join(scripts_dir, json_filename)

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"找不到指定的文本脚本文件: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        text_script = f.read()
    json_script = parse_text_script(text_script)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_script, f, ensure_ascii=False, indent=2)
    return json_output_path

if __name__ == "__main__":
    # 默认脚本文件名
    filename = "C:\\Users\\20232\\OneDrive\\大三上\\程序设计与实践\\大作业\\项目文件\\CSBotInterpreter\\scripts\\jd_service_script.txt"
    json_path = text_script_to_json_file(filename)
    print(f"已生成JSON脚本文件: {json_path}")
