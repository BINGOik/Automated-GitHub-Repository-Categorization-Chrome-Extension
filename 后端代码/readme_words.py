import re
from collections import Counter

# 英文停用词（够用版；你也可以自己扩充）
STOPWORDS = {
    "a","an","the","and","or","but","if","then","else","when","while","for","to","of","in","on","at","by","from",
    "with","without","as","is","are","was","were","be","been","being","this","that","these","those","it","its",
    "you","your","we","our","they","their","he","she","his","her","them","us","i","me","my",
    "can","could","may","might","must","shall","should","will","would",
    "do","does","did","done","doing","have","has","had","having",
    "not","no","yes","true","false","all","any","some","more","most","much","many",
    "about","into","over","under","up","down","out","off","again","further","here","there",
    "than","too","very","also","such","only","own","same","so","too",
    "use","using","used","make","makes","made","support","supports","supported",
    "project","repo","repository","readme","documentation","docs","example","examples",
}

def extract_keywords_from_readme(
    text: str,
    *,
    keep_top_k: int = 400,       # 最多保留多少关键词（避免太长）
    min_len: int = 2,            # 词最短长度
    keep_numbers: bool = False,  # 是否保留纯数字
) -> str:
    """
    不用大模型：把 README 文本的词当关键词。
    返回：空格分隔的 keyword 串（可直接喂给你的 SVM predictor）。
    """

    if not text:
        return ""

    # 1) 去掉代码块（``` ... ```），避免把代码变量名/路径刷屏
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)

    # 2) 去掉行内代码 `...`
    text = re.sub(r"`[^`]*`", " ", text)

    # 3) 去掉 URL
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 4) 去掉 Markdown 链接语法 [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 5) 标准化：小写
    text = text.lower()

    # 6) 只保留字母数字和空格（其他都换空格）
    text = re.sub(r"[^a-z0-9\s]+", " ", text)

    # 7) 分词
    tokens = text.split()

    # 8) 过滤停用词、短词、纯数字
    cleaned = []
    for w in tokens:
        if len(w) < min_len:
            continue
        if (not keep_numbers) and w.isdigit():
            continue
        if w in STOPWORDS:
            continue
        cleaned.append(w)

    if not cleaned:
        return ""

    # 9) 词频统计：只取高频 top_k，避免字符串太长导致你后面处理慢
    freq = Counter(cleaned)
    top_words = [w for w, _ in freq.most_common(keep_top_k)]

    # 10) 输出成空格分隔的关键词串
    return " ".join(top_words)
