from openai import OpenAI
import os
import re

# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-623f2c0e9f6a4efea4031dc65a87c378",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 常量：大模型初始化信息
MODEL_INIT_PROMPT = "你是一个用户意图识别器。你的任务是通过用户的自然语言输入，识别他们的意图。用户的意图只能是以下几种情况："

def extract_branches(script_path: str) -> list:
    """
    辅助函数：从脚本文件中提取所有可能的意图（Branch 分支名），去重。
    :param script_path: 文本脚本文件路径
    :return: 去重后的分支名列表（不包含 "意图识别失败"）
    """
    branches = set()  # 使用集合存储，自动去重
    with open(script_path, "r", encoding="utf-8") as file:
        for line in file:
            # 匹配 Branch "<关键词>", <stepName>
            match = re.search(r'Branch\s+"(.+?)"', line)
            if match:
                branch_name = match.group(1)
                if branch_name != "意图识别失败":
                    branches.add(branch_name)  # 添加到集合中
    return list(branches)  # 转换为列表返回

def recognize_intent(user_input: str, possible_intents: list) -> str:
    """
    核心函数：调用大模型 API 识别用户意图。
    :param user_input: 用户的自然语言输入
    :param possible_intents: 可能的意图列表
    :return: 识别出的意图（或 "意图识别失败"）
    """
    # 拼接初始化信息
    prompt = MODEL_INIT_PROMPT + "、".join(possible_intents) + "。"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input}
    ]
    print(f"[DEBUG] 发送给大模型的消息: {messages}")
    try:
        # 调用大模型 API
        response = client.chat.completions.create(
            model="deepseek-v3.2-exp",
            messages=messages,
            extra_body={"enable_thinking": False},
            stream=False
        )
        # 打印完整响应内容以调试
        print(f"[DEBUG] 大模型返回的完整响应: {response}")

        # 提取返回的意图
        intent = response.choices[0].message.content.strip()
        if intent not in possible_intents:
            return "意图识别失败"
        return intent
    except Exception as e:
        print(f"[ERROR] 意图识别失败: {e}")
        return "意图识别失败"

def main():
    """
    主函数：测试辅助函数和核心函数。
    """
    # 示例脚本路径
    script_path = "/Users/fangwuxinyuan/Library/CloudStorage/OneDrive-个人/大三上/程序设计与实践/大作业/项目文件/CSBotInterpreter/scripts/jd_service_script.txt"
    user_input = "这个东西我不想要了"

    # 提取脚本中的可能意图
    possible_intents = extract_branches(script_path)
    print(f"可能的意图: {possible_intents}")

    # 调用大模型识别用户意图
    intent = recognize_intent(user_input, possible_intents)
    print(f"识别的用户意图: {intent}")

if __name__ == "__main__":
    main()