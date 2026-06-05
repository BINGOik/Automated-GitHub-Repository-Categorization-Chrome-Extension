import os
import re
import glob
import pandas as pd

# 整合大小模型预测结果
# 参数：
#   folder_path (str): 包含大模型交互矫正结果的文件夹路径。
#   file (str): 小模型确定的分类结果文件路径。
#   output_file (str): 拼接后的输出文件路径。
def get_final_results(folder_path, file, output_file):
    # 定义可能的分类结果列表
    categories = [
        "Desktop Application",
        "AI and Machine Learning Application",
        "WeChat Application Development",
        "Enterprise Application",
        "Web Application",
        "Mobile Application",
        "Code Development Tools or Plugin",
        "Server Application",
        "Game Development",
        "Application Plugin",
        "Others",
        "未分类"
    ]

    # 构造一个正则，用于匹配上述分类中的任何一个
    pattern = re.compile(r"(" + "|".join(re.escape(cat) for cat in categories) + r")")

    # 存储分类结果的列表
    data = []

    # 遍历所有以数字命名的 txt 文件
    for file_path in glob.glob(os.path.join(folder_path, "*.txt")):
        file_name = os.path.basename(file_path)
        file_id, ext = os.path.splitext(file_name)
        # 仅处理文件名是数字的 txt 文件
        if not file_id.isdigit():
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        # 在第一行中搜索分类结果
        match = pattern.search(first_line)
        if match:
            cat = match.group(1)
        else:
            cat = '未分类'

        # 将文件id和分类结果添加到数据列表
        data.append((int(file_id), cat))

    # 按 id 升序排序
    data.sort(key=lambda x: x[0])

    # 将数据转换为 DataFrame 格式
    df1 = pd.DataFrame(data, columns=['id', 'result'])

    # 读取第二个文件，并保留所需的列
    df2 = pd.read_excel(file)
    df2 = df2[['id', 'Top1 Class']]
    df2 = df2.rename(columns={'Top1 Class': 'result'})

    # 拼接两个 DataFrame
    concatenated_df = pd.concat([df1, df2], ignore_index=True)

    # 按 'id' 升序排列，并去除重复的行
    concatenated_df = concatenated_df.sort_values(by='id', ascending=True).drop_duplicates(subset='id', keep='first')

    # 保存为新的 Excel 文件
    concatenated_df.to_excel(output_file, index=False)

    print(f"拼接并排序后的文件已保存: {output_file}")

if __name__ == "__main__":
    # 示例调用
    folder_path = "大模型交互矫正结果-ds"
    file = '附件5：certain（小模型确定的分类）.xlsx'
    output_file = '附件8：最终预测结果-ds.xlsx'

    get_final_results(folder_path, file, output_file)
