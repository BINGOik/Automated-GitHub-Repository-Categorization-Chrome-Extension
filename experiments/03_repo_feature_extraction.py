import requests
import pandas as pd

# 读取 txt 文件中每行的 GitHub 仓库 URL，爬取所有仓库的语言信息并计算比例，最终将结果汇总到一个 Excel 文件中。
# 参数：
#   github_token: str, GitHub 个人访问 Token
#   txt_file: str, 存放仓库 URL 列表的 txt 文件路径
#   output_file: str, 最终输出的 Excel 文件路径
def get_languages(github_token, txt_file, output_file):
    records = []
    max_langs = 0

    # 1. 逐行读取 URL 并爬取语言数据
    with open(txt_file, 'r') as f:
        for line in f:
            repo_url = line.strip()
            if not repo_url:
                continue

            # 提取仓库拥有者和仓库名
            try:
                owner, name = repo_url.rstrip('/').split('/')[-2:]
            except ValueError:
                print(f"[WARN] 无效的 URL：{repo_url}")
                continue

            # 请求 GitHub API 获取语言数据
            api_url = f'https://api.github.com/repos/{owner}/{name}/languages'
            headers = {'Authorization': f'token {github_token}'}
            resp = requests.get(api_url, headers=headers)
            if resp.status_code != 200:
                print(f"[WARN] 仓库 {owner}/{name} 获取失败，状态码：{resp.status_code}")
                continue

            langs = resp.json()
            total_bytes = sum(langs.values())
            if total_bytes == 0:
                print(f"[INFO] 仓库 {owner}/{name} 无语言数据。")
                continue

            # 排序并构造记录
            sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
            max_langs = max(max_langs, len(sorted_langs))

            row = {'repo_owner': owner, 'repo_name': name}
            for idx, (lang, byte_count) in enumerate(sorted_langs, start=1):
                row[f'bytes_{idx}'] = byte_count
                row[f'language_{idx}'] = lang
                row[f'proportion_{idx}'] = byte_count / total_bytes
            records.append(row)

    if not records:
        print("未获取到任何有效仓库数据。")
        return

    # 2. 构建 DataFrame，并补齐缺失列
    df = pd.DataFrame(records)
    for idx in range(1, max_langs + 1):
        for col in (f'bytes_{idx}', f'language_{idx}', f'proportion_{idx}'):
            if col not in df.columns:
                df[col] = 0

    # 3. 重新排序列：repo_owner, repo_name, 再到 bytes_1, language_1, proportion_1, ...
    cols = ['repo_owner', 'repo_name']
    for idx in range(1, max_langs + 1):
        cols += [f'bytes_{idx}', f'language_{idx}', f'proportion_{idx}']
    df = df[cols]

    # 4. 导出到 Excel
    df.to_excel(output_file, index=False)
    print(f"所有仓库数据已保存到 '{output_file}'")


if __name__ == '__main__':
    # 使用示例
    github_token = 'access_token'
    txt_file = 'URLs.txt'
    output_file = '基本特征_languages.xlsx'
    get_languages(github_token, txt_file, output_file)
