import os
import re
import pandas as pd

# 从指定文件中提取匹配预定义关键词的标题。
# 参数:
#   file_path (str): 目标文本文件路径。
#   keywords (list): 关键字列表，用于匹配标题。
# 返回值: 提取到的标题列表（小写）。
def get_headers(file_path, keywords):
    found_keywords = []
    # 定义三种标题匹配模式：Markdown、编号和下划线风格
    header_patterns = [
        rf'^#+\s*({'|'.join(keywords)})\b',       # Markdown 级标题，如 # Usage、## Usage
        rf'^\d+\.\s*({'|'.join(keywords)})\b',    # 有序列表标题，如 1. Usage
        rf'^\s*({'|'.join(keywords)})\s*\n[-=]+'    # 下划线风格标题，如 Contributors\n---------
    ]
    header_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in header_patterns]

    # 逐行读取并匹配标题
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for i in range(len(lines) - 1):
            line = lines[i].strip().lower()
            for pattern in header_patterns:
                if pattern.match(line) or pattern.match(line + '\n' + lines[i + 1].strip()):
                    found_keywords.append(line)
                    break
    return found_keywords


# 统计文件中基于 ``` 标识的代码块数（成对计数）
# 参数:
#   file_path (str): 文本文件路径。
# 返回值: 代码块数量
def count_code_blocks(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        return content.count("```") // 2


# 统计文件中 HTTP(S)、www 或 Markdown 链接的出现次数。
# 参数:
#   file_path (str): 文本文件路径。
# 返回值: 链接出现次数。
def count_links(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().lower()
        return len(re.findall(r'(http[s]?://|www\.|]\(http)', content))

# 检查文件内容中是否包含指定关键字列表中的任意一个。
# 参数:
#   file_path (str): 文本文件路径。
#   keyword_list (list): 关键字列表。
# 返回值: 是否包含任一关键字。
def check_keywords(file_path, keyword_list):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().lower()
        return any(keyword in content for keyword in keyword_list)


# 获取文件内容的字符总数。
# 参数:
#   file_path (str): 文本文件路径。
# 返回值: 字符数。
def get_file_length(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return len(f.read())


# 主函数：读取readme并生成结构特征Excel表格
# 参数:
#   extraction_dir (str): 存放README文件的目录路径。
#   output_path (str): 输出结构特征Excel文件路径。
def get_structure_feature(extraction_dir, output_path):
    # 在函数内部定义默认关键词列表
    header_keywords = [
        'how to use', 'usage', 'setup', 'installation', 'build',
        'contributing', 'contact', 'author', 'report bug'
    ]
    api_keywords = ['api']
    doc_keywords = ['documentation', 'docs']

    results = []
    # 遍历目录中的所有 .txt 文件
    for filename in os.listdir(extraction_dir):
        if filename.lower().endswith('.txt'):
            file_id = int(os.path.splitext(filename)[0])
            file_path = os.path.join(extraction_dir, filename)
            # 提取各项指标
            headers = get_headers(file_path, header_keywords)
            length = get_file_length(file_path)
            code_blocks = count_code_blocks(file_path)
            links = count_links(file_path)
            has_api = check_keywords(file_path, api_keywords)
            has_docs = check_keywords(file_path, doc_keywords)

            # 构建结果行
            row = {
                'id': file_id,
                'file_length': length,
                'code_block_count': code_blocks,
                'link_count': links,
                'api': 1 if has_api else 0,
                'documentation': 1 if has_docs else 0
            }
            # 添加标题存在标识
            for kw in header_keywords:
                row[kw] = 1 if kw in headers else 0
            results.append(row)

    # 转换为 DataFrame 并按 id 排序
    df = pd.DataFrame(results)
    if not df.empty:
        df.sort_values('id', inplace=True)
    # 写入 Excel 文件
    df.to_excel(output_path, index=False)
    print(f"README 综合分析已保存至：{output_path}")

if __name__ == '__main__':
    # 使用示例
    extraction_dir = "readme"
    output_path = "附件3：结特征.xlsx"
    get_structure_feature(extraction_dir, output_path)
