import os
from concurrent.futures import ThreadPoolExecutor
import openai

# 与 OpenAI API 交互以生成标签的函数
# 参数:
#   messages: 消息列表，每个元素为字典，包含 role 和 content
#   model: 模型名称字符串，默认为 "gpt-4o-mini"
def chatgpt_api(messages, model="gpt-4o-mini"):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API 请求错误: {e}")
        return None

# 主处理函数
# 参数:
#   model: 用于生成标签的模型名称
#   input_folder: 存放README文件的输入目录
#   output_folder: 输出keyword的目标目录
#   api_key: 环境变量名，用于读取 API Key
#   checkpoint_file: 用于记录已处理文件名的检查点文件，默认为 "checkpoint.txt"
#   max_workers: 并发线程数，默认为 4
def chatgpt_keyword(model, input_folder, output_folder, api_key="OPENAI_API_KEY", checkpoint_file="checkpoint.txt", max_workers=4):
    # 设置代理
    os.environ.update({
        "http_proxy": "http://localhost:7890",
        "https_proxy": "http://localhost:7890"
    })
    print("已设置代理：http://localhost:7890")

    # 设置 API Key
    key = os.getenv(api_key)
    if not key:
        raise ValueError(f"环境变量 {api_key} 未找到，请配置 API Key。")
    openai.api_key = key
    print(f"已从环境变量 {api_key} 设置 API Key。")

    # 确保输出目录存在
    os.makedirs(output_folder, exist_ok=True)

    # 加载已处理文件列表
    processed_files = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as cf:
            processed_files = set(cf.read().splitlines())

    # 收集所有待处理的 .txt 文件
    files_to_process = [f for f in os.listdir(input_folder) if f.endswith(".txt")]

    # 内部函数: 处理单个文件
    def _process_file(filename):
        if filename in processed_files:
            print(f"跳过 {filename}，已处理。")
            return

        input_path = os.path.join(input_folder, filename)
        # 读取项目描述
        with open(input_path, "r", encoding="utf-8") as infile:
            project_description = infile.read().strip()

        # 构建请求消息
        messages = [
            {"role": "system", "content": (
                "你是一个开源软件项目的标签标注员，负责根据项目描述自动生成适合的 GitHub 标签。"
                "请根据给定的项目描述，结合 GitHub 标签的惯例，为该项目分配标签。标签应该简洁、相关，"
                "并能准确反映项目的主要特点。输出的格式应为：tag1 tag2 tag3...，多个标签之间用空格分隔。"
                "若文本过短无法提取标签则输出 none。请确保标签的数量和准确性，以便更好地描述项目的性质。"
            )},
            {"role": "user", "content": f"Project description: {project_description}"}
        ]

        # 调用 API 生成标签
        tags = chatgpt_api(messages, model)
        if not tags:
            print(f"{filename} 生成标签失败。")
            return

        # 写入输出文件
        output_path = os.path.join(output_folder, filename)
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(tags)

        # 更新检查点文件
        with open(checkpoint_file, "a", encoding="utf-8") as cf:
            cf.write(f"{filename}\n")

        print(f"{filename} 的标签已成功保存。")

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for fname in files_to_process:
            executor.submit(_process_file, fname)

    print("所有任务已完成。")

# 示例用法
if __name__ == "__main__":
    # 调用主函数，无需传入 openai 模块
    chatgpt_keyword(
        model="gpt-4o-mini",
        input_folder="readme",
        output_folder="keyword-GPT"
    )
