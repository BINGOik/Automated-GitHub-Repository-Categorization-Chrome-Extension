import os
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_score, accuracy_score, f1_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

#使用指定模型训练分类器，并进行交叉验证
# 参数:
#   main_data_path (str): 结构化特征 Excel 文件路径
#   language_data_path (str): 语言特征 Excel 文件路径
#   npy_folder_path (str): 存放语义特征 .npy 文件的文件夹路径
#   model_type (str): 使用的模型类型，可以选择 'xgboost', 'decision_tree', 'random_forest', 'naive_bayes', 'linear_svc', 'logistic_regression'
#   use_structural (bool): 是否使用结构特征
#   use_language (bool): 是否使用基本特征(包括 keyword)
#   use_semantic (bool): 是否使用语义特征(.npy)
#   n_splits (int): 交叉验证折数
#   random_state (int): 随机种子
def train_model(main_data_path, language_data_path, npy_folder_path, model_type = 'xgboost', use_structural = True, use_language = True, use_semantic= True, n_splits = 10, random_state: int = 42):
    # 1. 读取结构特征和语言特征数据
    main_df = pd.read_excel(main_data_path)
    lang_df = pd.read_excel(language_data_path)
    df = pd.merge(main_df, lang_df, on='id', how='left')

    y = df['result']
    feature_matrices = []

    # 2. 处理结构特征
    if use_structural:
        struct_cols = [c for c in df.columns if
                       c not in ['id', 'result'] and not c.startswith('language_') and c != 'keyword']
        X_struct = csr_matrix(df[struct_cols].fillna(0).values)
        feature_matrices.append(X_struct)

    # 3. 处理基本特征（One-Hot 编码）
    if use_language:
        lang_cols = [c for c in df.columns if c.startswith('language_')]
        if lang_cols:
            oe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
            lang_encoded = oe.fit_transform(df[lang_cols].astype(str).fillna('Unknown'))
            feature_matrices.append(csr_matrix(lang_encoded))

        if 'keyword' in df.columns:
            kw_split = df['keyword'].fillna('').apply(lambda x: x.split())
            unique_kw = set(k for kws in kw_split for k in kws)
            kw_idx = {k: i for i, k in enumerate(unique_kw)}

            def encode_kws(kws_list):
                vec = np.zeros(len(kw_idx), dtype=int)
                for kw in kws_list:
                    vec[kw_idx[kw]] = 1
                return vec

            kw_mat = csr_matrix(np.vstack(kw_split.apply(encode_kws).values))
            feature_matrices.append(kw_mat)

    # 4. 处理语义特征 (.npy 文件)
    if use_semantic:
        sem_list = []
        default_len = None
        for idx in df['id']:
            file_path = os.path.join(npy_folder_path, f"{idx}.npy")
            if os.path.exists(file_path):
                arr = np.load(file_path)
                if default_len is None:
                    default_len = arr.size
                sem_list.append(arr)
            else:
                sem_list.append(np.zeros(default_len or 0))
        sem_mat = csr_matrix(np.vstack(sem_list))
        feature_matrices.append(sem_mat)

    # 5. 合并所有特征矩阵
    X_all = hstack(feature_matrices, format='csr')

    # 6. 归一化处理
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_all.toarray())
    X = csr_matrix(X_scaled)

    # 7. 目标变量编码
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # 8. 选择模型
    if model_type == 'xgboost':
        model = XGBClassifier(eval_metric='mlogloss', use_label_encoder=False, random_state=random_state)
    elif model_type == 'decision_tree':
        model = DecisionTreeClassifier(random_state=random_state)
    elif model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=random_state)
    elif model_type == 'naive_bayes':
        model = GaussianNB()
    elif model_type == 'linear_svc':
        model = LinearSVC(max_iter=5000, C=0.1, random_state=42)
    elif model_type == 'logistic_regression':
        model = LogisticRegression(max_iter=5000, random_state=random_state)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # 9. 交叉验证训练与评估
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    precision_list, accuracy_list, f1_list = [], [], []

    for fold, (train_idx, test_idx) in enumerate(kf.split(X, y_enc), start=1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_enc[train_idx], y_enc[test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        precision_list.append(precision_score(y_test, y_pred, average='weighted', zero_division=1))
        accuracy_list.append(accuracy_score(y_test, y_pred))
        f1_list.append(f1_score(y_test, y_pred, average='weighted', zero_division=1))

        print(
            f"Fold {fold} - Precision: {precision_list[-1]:.4f}, Accuracy: {accuracy_list[-1]:.4f}, F1: {f1_list[-1]:.4f}")

    # 10. 汇总结果
    results = {
        'per_fold': [
            {'precision': p, 'accuracy': a, 'f1': f}
            for p, a, f in zip(precision_list, accuracy_list, f1_list)
        ],
        'average': {
            'precision': np.mean(precision_list),
            'accuracy': np.mean(accuracy_list),
            'f1': np.mean(f1_list)
        }
    }

    # 11. 保存评估结果到文本文件
    with open(f"{model_type}_results.txt", 'w') as f_out:
        for i, metrics in enumerate(results['per_fold'], start=1):
            f_out.write(
                f"Fold {i} - Precision: {metrics['precision']:.4f}, "
                f"Accuracy: {metrics['accuracy']:.4f}, F1 Score: {metrics['f1']:.4f}\n"
            )

    return results


if __name__ == '__main__':
    # 示例调用：选择不同模型进行训练
    res = train_model(
        main_data_path='附件3：结特征.xlsx',
        language_data_path='附件2：基本特征-GPT.xlsx',
        npy_folder_path='codeBERT',
        model_type='random_forest',  # 选择模型类型
        use_structural=True,
        use_language=True,
        use_semantic=True
    )
    print('平均指标:', res['average'])
