import joblib
import numpy as np
from scipy.sparse import csr_matrix

class Predictor:
    def __init__(self,
                 model_path='linear_svc_model.pkl',
                 label_mapping_path='label_mapping.pkl',
                 scaler_path='scaler.pkl',
                 keyword_dict_path='keyword_dict.pkl'):
        self.clf = joblib.load(model_path)
        self.label_mapping = joblib.load(label_mapping_path)
        self.scaler = joblib.load(scaler_path)
        self.keyword_dict = joblib.load(keyword_dict_path)
        self.class_labels = [self.label_mapping[i] for i in range(len(self.label_mapping))]

    @staticmethod
    def softmax(x):
        x_exp = np.exp(x - np.max(x))
        return x_exp / np.sum(x_exp)

    def one_hot_encode_keywords(self, keywords):
        one_hot_vector = [0] * len(self.keyword_dict)
        for keyword in keywords:
            if keyword in self.keyword_dict:
                one_hot_vector[self.keyword_dict[keyword]] = 1
        return one_hot_vector

    def predict_from_keyword(self, keyword_str, topn=None):
        encoded = self.one_hot_encode_keywords(keyword_str.strip().split())
        X_dense = csr_matrix([encoded])
        X_scaled = self.scaler.transform(X_dense.toarray())
        X_final = csr_matrix(X_scaled)

        # ✅ 兼容 binary / multiclass：统一成 (1, n_classes)
        raw = self.clf.decision_function(X_final.toarray())

        raw = np.asarray(raw)
        if raw.ndim == 1:
            # binary: shape (n_samples,) -> (n_samples, 2)
            # 对 LinearSVC 二分类：用 [-score, score] 当作两个类别的logit
            raw = np.vstack([-raw, raw]).T

        scores = raw[0]  # shape (n_classes,)
        probs = self.softmax(scores)  # shape (n_classes,)

        sorted_indices = np.argsort(probs)[::-1]
        result = [
            {'class': self.class_labels[idx], 'prob': float(probs[idx])}
            for idx in sorted_indices
        ]
        if topn:
            result = result[:topn]
        return result
