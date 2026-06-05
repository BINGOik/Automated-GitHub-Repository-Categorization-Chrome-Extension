import numpy as np
import pytest


pytestmark = pytest.mark.unit


class DummyScaler:
    def __init__(self):
        self.seen = None

    def transform(self, matrix):
        self.seen = matrix
        return matrix


class DummyModel:
    def __init__(self, scores):
        self.scores = np.asarray(scores)

    def decision_function(self, matrix):
        return np.asarray([self.scores])


class DummyBinaryModel:
    def __init__(self, score):
        self.score = score

    def decision_function(self, matrix):
        return np.asarray([self.score])


def build_predictor(module, monkeypatch, *, scores, labels=None, keyword_dict=None):
    scaler = DummyScaler()
    labels = labels or {0: "网页应用", 1: "应用插件", 2: "其他"}
    keyword_dict = keyword_dict or {"react": 0, "flask": 1, "chrome": 2}

    objects = {
        "model.pkl": DummyModel(scores),
        "labels.pkl": labels,
        "scaler.pkl": scaler,
        "keywords.pkl": keyword_dict,
    }

    monkeypatch.setattr(module.joblib, "load", lambda path: objects[path])
    predictor = module.Predictor("model.pkl", "labels.pkl", "scaler.pkl", "keywords.pkl")
    return predictor, scaler


def test_softmax_returns_probabilities_that_sum_to_one(svm_predictor_module):
    probs = svm_predictor_module.Predictor.softmax(np.array([1.0, 2.0, 3.0]))

    assert pytest.approx(float(np.sum(probs)), rel=1e-7) == 1.0
    assert probs.argmax() == 2


def test_predictor_builds_class_labels_from_label_mapping(svm_predictor_module, monkeypatch):
    predictor, _ = build_predictor(
        svm_predictor_module,
        monkeypatch,
        scores=[0.1, 0.2, 0.3],
        labels={0: "A", 1: "B", 2: "C"},
    )

    assert predictor.class_labels == ["A", "B", "C"]


def test_one_hot_encode_keywords_marks_known_keywords(svm_predictor_module, monkeypatch):
    predictor, _ = build_predictor(svm_predictor_module, monkeypatch, scores=[0.1, 0.2, 0.3])

    vector = predictor.one_hot_encode_keywords(["react", "chrome"])

    assert vector == [1, 0, 1]


def test_one_hot_encode_keywords_ignores_unknown_keywords(svm_predictor_module, monkeypatch):
    predictor, _ = build_predictor(svm_predictor_module, monkeypatch, scores=[0.1, 0.2, 0.3])

    vector = predictor.one_hot_encode_keywords(["unknown", "flask"])

    assert vector == [0, 1, 0]


def test_predict_from_keyword_sorts_multiclass_probabilities(svm_predictor_module, monkeypatch):
    predictor, scaler = build_predictor(
        svm_predictor_module,
        monkeypatch,
        scores=[0.1, 3.0, 1.0],
        labels={0: "网页应用", 1: "应用插件", 2: "其他"},
    )

    result = predictor.predict_from_keyword("react flask unknown", topn=2)

    assert [item["class"] for item in result] == ["应用插件", "其他"]
    assert result[0]["prob"] > result[1]["prob"]
    assert scaler.seen.shape == (1, 3)


def test_predict_from_keyword_supports_binary_decision_function(
    svm_predictor_module, monkeypatch
):
    scaler = DummyScaler()
    objects = {
        "model.pkl": DummyBinaryModel(2.0),
        "labels.pkl": {0: "非插件", 1: "应用插件"},
        "scaler.pkl": scaler,
        "keywords.pkl": {"chrome": 0},
    }
    monkeypatch.setattr(svm_predictor_module.joblib, "load", lambda path: objects[path])
    predictor = svm_predictor_module.Predictor(
        "model.pkl", "labels.pkl", "scaler.pkl", "keywords.pkl"
    )

    result = predictor.predict_from_keyword("chrome", topn=1)

    assert result[0]["class"] == "应用插件"
    assert 0.0 <= result[0]["prob"] <= 1.0
