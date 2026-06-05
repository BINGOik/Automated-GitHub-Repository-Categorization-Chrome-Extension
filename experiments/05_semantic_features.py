import os
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np

# 从 folder_path 中的所有 .txt 文件提取特征（[CLS] 嵌入）并保存为 .npy 文件。
# 参数:
#   model_name (str): "robertalarge" 或 "codebert"
#   folder_path (str): 包含 .txt 文件的文件夹路径
# 返回值: 无。
def get_language_features(model_name, folder_path):
    # 根据 model_name 选择预训练模型
    model_map = {
        "robertalarge": "facebookai/roberta-large",
        "codebert": "microsoft/codebert-base"
    }
    if model_name not in model_map:
        raise ValueError(f"未知的 model_name: {model_name}，仅支持 {list(model_map.keys())}")

    pretrained_id = model_map[model_name]
    print(f"加载模型: {pretrained_id}")

    tokenizer = AutoTokenizer.from_pretrained(pretrained_id)
    model = AutoModel.from_pretrained(pretrained_id)
    model.eval()

    def extract_cls_embedding(text: str):
        """对单条文本获取 [CLS] 嵌入向量"""
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()

    # 遍历文件夹
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".txt"):
            continue
        txt_path = os.path.join(folder_path, filename)
        print(f"正在处理 {filename} ...")
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
        embedding = extract_cls_embedding(text)

        npy_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}.npy")
        np.save(npy_path, embedding)
        print(f"已保存: {npy_path}")

    print("所有文件特征已保存。")


if __name__ == "__main__":
    # 示例调用
    # get_language_features(model_name="robertalarge", folder_path="readme")
    # 或者使用 CodeBERT：
    get_language_features(model_name="codebert", folder_path="readme")
