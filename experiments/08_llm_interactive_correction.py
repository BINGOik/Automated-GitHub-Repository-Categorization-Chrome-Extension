import os
from concurrent.futures import ThreadPoolExecutor
import openai
import pandas as pd

# 大模型针对不确定的项目进行矫正
# 参数：
#   excel_file: 包含不确定的项目 id 及预测结果的 Excel 文件路径
#   readme_folder: 存放 README 文本文件的文件夹路径，文件命名格式 {id}.txt
#   output_folder: 输出分类结果的文件夹路径
#   checkpoint_file: 存储已处理项目 id 的文件路径
#   api_key: OpenAI API 密钥
#   proxy: 可选，http/https 代理地址，如 "http://localhost:7890"
#   model: 使用的模型名称，默认为 gpt-4o-mini
#   max_workers: 并发线程数，默认为 10
def chatgpt_classification(excel_file, readme_folder, output_folder, checkpoint_file, api_key, proxy = None, model = "gpt-4o-mini", max_workers = 10):
    # 设置代理（如需）
    if proxy:
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy

    # 设置 OpenAI API 密钥
    openai.api_key = api_key

    # 创建输出目录
    os.makedirs(output_folder, exist_ok=True)

    # 读取已处理 id
    processed_ids = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as cp_f:
            processed_ids = set(cp_f.read().splitlines())

    # 读取 Excel 文件
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"无法读取 Excel 文件: {e}")
        return

    def process_row(row):
        project_id = str(row['id'])
        # 如果已经处理，跳过
        if project_id in processed_ids:
            print(f"跳过项目 {project_id}，已处理。")
            return

        # 构建预测结果字符串
        predictions = []
        for i in range(1, 13):
            cls_col = f"Top{i} Class"
            prob_col = f"Top{i} Probability"
            if cls_col in row and pd.notna(row[cls_col]) and prob_col in row and pd.notna(row[prob_col]):
                predictions.append(f"Top{i}: {row[cls_col]} ({row[prob_col]})")
        predictions_str = ", ".join(predictions)

        # 读取 README 内容
        readme_path = os.path.join(readme_folder, f"{project_id}.txt")
        if not os.path.exists(readme_path):
            print(f"README 文件 {project_id}.txt 未找到，跳过。")
            return
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read().strip()

        # 构建系统提示
        system_prompt = (
            "You are a open source project's development domain classifier. "
            "Your task is to classify the domain of a software development project according "
            "to the following text of the project description and README files. Categories include: "
            "(1) Desktop Application; (2) AI and Machine Learning Application; (3) WeChat Application Development; "
            "(4) Enterprise Application; (5) Web Applications; (6) Mobile Application; (7) Code Development Tools or Plugin; "
            "(8) Server Application; (9) Game Development; (10) Application Plugin; (11) Others; (12)未分类 "
            "The current model predictions for this project are as follows - " + predictions_str + ". "
            "We believe there may be issues with the labeling. Please relabel this project according to its actual "
            "application scope. Please provide the Result: and Reasons: " + readme_content
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"project ID: {project_id}"}
        ]

        # 调用 OpenAI 接口
        try:
            resp = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0
            )
            answer = resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"项目 {project_id} API 调用失败: {e}")
            return

        # 写入输出文件
        out_path = os.path.join(output_folder, f"{project_id}.txt")
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(answer)

        # 更新已处理列表
        with open(checkpoint_file, "a", encoding="utf-8") as cp_f:
            cp_f.write(f"{project_id}\n")

        print(f"项目 {project_id} 处理完成。")

    # 并发处理所有项目
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for _, row in df.iterrows():
            executor.submit(process_row, row)


if __name__ == "__main__":
    # 示例调用
    chatgpt_classification(
        excel_file="附件6：uncertain（小模型不确定的分类）.xlsx",
        readme_folder="readme",
        output_folder="大模型交互矫正结果",
        checkpoint_file="checkpoint-2.txt",
        api_key="***",
        proxy="http://localhost:7890"
    )
