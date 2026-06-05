import os
import numpy as np
import pandas as pd
from scipy.special import softmax
from scipy.sparse import csr_matrix, hstack
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder
from sklearn.svm import LinearSVC
from sklearn.metrics import precision_score, accuracy_score, f1_score

# 载入数据、训练 LinearSVC 并输出 Softmax 概率结果
# 参数：
#   main_data_path: 结构特征 Excel 文件路径
#   language_data_path: 基本特征 Excel 文件路径
#   npy_folder_path: 存放 .npy 语义特征文件的文件夹路径
#   output_path: 保存 TopK 概率输出的 Excel 文件名
#   uncertain_path: 保存“不确定组”输出的 Excel 文件名
#   certain_path: 保存“确定组”输出的 Excel 文件名
#   uncertain_threshold: Top1 与 Top2 概率差值阈值，用于划分“不确定组”
#   n_splits: 交叉验证折数
#   random_state: 随机种子

def svm_prob(main_data_path, language_data_path, npy_folder_path, output_path = 'probability.xlsx', uncertain_path = '附件6：uncertain（小模型不确定的分类）.xlsx', certain_path = '附件5：certain（小模型确定的分类）.xlsx', uncertain_threshold = 0.15, n_splits = 10, random_state = 42):

    # 1. 加载主数据和语言数据
    data = pd.read_excel(main_data_path)
    language_data = pd.read_excel(language_data_path)

    # 2. 合并数据集
    merged = pd.merge(data, language_data, on='id', how='left')

    # 3. 分离特征和标签
    X = merged.drop(columns=['id', 'result'])
    y = merged['result']

    # 4. 处理语言特征：One-Hot 编码
    lang_cols = [c for c in X.columns if c.startswith('language_')]
    ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    lang_enc = ohe.fit_transform(X[lang_cols].astype(str).fillna('Unknown'))
    X = X.drop(columns=lang_cols)

    # 5. 转换其余普通特征为稠密矩阵（去掉 keyword 列）
    X_dense = csr_matrix(X.drop(columns=['keyword']).values)

    # 6. 处理 keyword 列：拆分后自定义 One-Hot
    keywords = X['keyword'].fillna('').apply(lambda s: s.split())
    unique_kw = {kw for kws in keywords for kw in kws}
    kw2idx = {kw: i for i, kw in enumerate(sorted(unique_kw))}

    def encode_kw(kws):
        vec = np.zeros(len(kw2idx), dtype=int)
        for w in kws:
            if w in kw2idx:
                vec[kw2idx[w]] = 1
        return vec

    kw_enc = np.vstack(keywords.apply(encode_kw).values)
    X_kw = csr_matrix(kw_enc)

    # 7. 加载 .npy 语义特征，并补齐缺失
    sem_feats = []
    feat_len = None
    for idx in merged['id']:
        path = os.path.join(npy_folder_path, f"{idx}.npy")
        if os.path.exists(path):
            arr = np.load(path)
            sem_feats.append(arr)
            if feat_len is None:
                feat_len = arr.shape[0]
        else:
            # 若找不到文件，则填零向量
            if feat_len is None:
                raise ValueError("首次加载语义特征时出错：未确定特征长度")
            sem_feats.append(np.zeros(feat_len, dtype=float))
    X_sem = csr_matrix(np.vstack(sem_feats))

    # 8. 合并所有特征
    X_all = hstack([X_dense, csr_matrix(lang_enc), X_kw, X_sem], format='csr')

    # 9. 归一化
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_all.toarray())
    X_final = csr_matrix(X_scaled)

    # 10. 编码标签
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 11. 交叉验证评估
    clf = LinearSVC(max_iter=5000, C=0.1, random_state=random_state)
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    precs, accs, f1s = [], [], []

    for fold, (tr, te) in enumerate(kf.split(X_final, y_enc), 1):
        clf.fit(X_final[tr], y_enc[tr])
        pred = clf.predict(X_final[te])
        precs.append(precision_score(y_enc[te], pred, average='weighted', zero_division=1))
        accs.append(accuracy_score( y_enc[te], pred))
        f1s.append(f1_score(  y_enc[te], pred, average='weighted', zero_division=1))
        print(f"Fold {fold}: Precision={precs[-1]:.4f}, Accuracy={accs[-1]:.4f}, F1={f1s[-1]:.4f}")

    print(f"Avg Precision: {np.mean(precs):.4f}, Avg Accuracy: {np.mean(accs):.4f}, Avg F1: {np.mean(f1s):.4f}")

    # 12. 全量重训练并计算 Softmax 概率
    clf.fit(X_final, y_enc)
    scores = clf.decision_function(X_final)
    probs  = softmax(scores, axis=1)

    # 13. 构建输出表格，提取 Top12
    K = 12
    classes = le.classes_
    topk_idx   = np.argsort(probs, axis=1)[:, ::-1][:, :K]
    topk_prob  = np.sort(probs, axis=1)[:, ::-1][:, :K]

    out = pd.DataFrame({
        'id': merged['id'],
        'True Label': merged['result']
    })
    for i in range(K):
        out[f'Top{i+1} Class']       = [classes[j] for j in topk_idx[:, i]]
        out[f'Top{i+1} Probability'] = topk_prob[:, i]

    # 14. 保存完整概率结果
    out.to_excel(output_path, index=False)
    print(f"Softmax 概率结果已保存到：{output_path}")

    # 15. 根据 Top1-Top2 差值拆分“确定组”和“不确定组”
    diff = out['Top1 Probability'] - out['Top2 Probability']
    out[diff < uncertain_threshold].to_excel(uncertain_path, index=False)
    out[diff >= uncertain_threshold].to_excel(certain_path, index=False)
    print(f"不确定组（差值<{uncertain_threshold}）已保存：{uncertain_path}，行数={len(out[diff<uncertain_threshold])}")
    print(f"确定组（差值>={uncertain_threshold}）已保存：{certain_path}，行数={len(out[diff>=uncertain_threshold])}")

# 示例调用
if __name__ == "__main__":
    svm_prob(
        main_data_path='附件3：结构特征.xlsx',
        language_data_path='附件2：基本特征-GPT.xlsx',
        npy_folder_path='codeBERT'
    )
