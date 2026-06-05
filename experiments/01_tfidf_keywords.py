import os
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# 提取每个 README 文件的前 N 个 keyword-TF-IDF 关键词，并将结果保存到指定的输出文件夹。
# 参数：
#   txt_folder (str): 输入的 README 文件所在目录路径。
#   output_folder (str): 提取结果文件保存的目录路径。
#   top_n (int): 每个文档提取关键词的数量，默认值为 10。
#   additional_stopwords (set, 可选): 额外的停用词集合。
#   nltk_data_path (str, 可选): NLTK 数据路径（如果需要手动指定）。
def tfidf_keyword(txt_folder, output_folder, top_n = 10, additional_stopwords = None, nltk_data_path = None):
    # 可选：配置 NLTK 数据路径
    if nltk_data_path:
        nltk.data.path.append(nltk_data_path)

    # 加载 NLTK 英语停用词
    nltk_stopwords = set(stopwords.words('english'))

    # 合并额外停用词（如果提供）
    if additional_stopwords:
        combined_stopwords = list(nltk_stopwords.union(additional_stopwords))
    else:
        combined_stopwords = list(nltk_stopwords)

    # 创建输出目录（如果不存在）
    os.makedirs(output_folder, exist_ok=True)

    # 遍历输入目录中的每个 .txt 文件
    for file_name in os.listdir(txt_folder):
        if not file_name.lower().endswith('.txt'):
            continue  # 跳过非 txt 文件

        file_path = os.path.join(txt_folder, file_name)
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            document = f.read()

        # 初始化 keyword-TF-IDF 向量器，设置停用词
        tfidf_vectorizer = TfidfVectorizer(stop_words=combined_stopwords)

        try:
            # 计算 keyword-TF-IDF 矩阵
            tfidf_matrix = tfidf_vectorizer.fit_transform([document])
            feature_names = tfidf_vectorizer.get_feature_names_out()

            # 如果没有有效特征词，则跳过
            if feature_names.size == 0:
                print(f"'{file_name}' 去除停用词后无有效词，已跳过。")
                continue

            # 获取非零 keyword-TF-IDF 分数及其索引
            feature_index = tfidf_matrix[0, :].nonzero()[1]
            scores = [(i, tfidf_matrix[0, i]) for i in feature_index]

            # 按分数降序排序并取前 top_n 项
            top_items = sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
            top_terms = [feature_names[i] for i, _ in top_items]

            # 将结果写入输出文件，每行一个关键词
            out_path = os.path.join(output_folder, f"{file_name}.keywords.txt")
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write('\n'.join(top_terms))

        except ValueError:
            # 处理空文档或全部为停用词的情况
            print(f"'{file_name}' 无法处理（空文档或全为停用词），已跳过。")

    print(f"提取完成，关键词已保存到 '{output_folder}'。")

# 示例用法：
if __name__ == "__main__":
    tfidf_keyword(
         txt_folder="readme",
         output_folder="keyword-TF-IDF",
         top_n=10,
         additional_stopwords={'http', 'https', 'www', 'see', 'please', 'may', 'also', 'can', 'based', 'need', 'following', 'first', 'new', 'simple', 'easily', 'just', 'actually', 'currently', 'would', 'readme', 'install'},
         nltk_data_path=r"D:\code\pythonProject\.venv\Lib\nltk_data\corpora\stopwords"
    )
