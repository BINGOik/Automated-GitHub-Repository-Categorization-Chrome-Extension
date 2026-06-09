import pytest


pytestmark = pytest.mark.integration


def test_end_to_end_high_confidence_svm_path(domain_module, fake_predictor_factory):
    domain_module.fetch_readme = lambda owner, repo: "# React\nFrontend web UI library."
    domain_module.extract_keywords_from_readme = lambda readme: "react frontend web ui"
    domain_module.predictor = fake_predictor_factory([
        {"class": "网页应用", "prob": 0.92},
        {"class": "代码开发工具或插件", "prob": 0.04},
    ])

    response = domain_module.app.test_client().post(
        "/domain",
        json={"owner": "facebook", "repo": "react"},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["result"] == "网页应用"
    assert data["svm_result"][0]["class"] == "网页应用"


def test_end_to_end_low_confidence_llm_refinement_path(
    domain_module, fake_predictor_factory
):
    domain_module.fetch_readme = lambda owner, repo: "# GitHub Badge Extension"
    domain_module.extract_keywords_from_readme = lambda readme: "github chrome extension badge"
    domain_module.predictor = fake_predictor_factory([
        {"class": "应用插件", "prob": 0.48},
        {"class": "代码开发工具或插件", "prob": 0.42},
    ])

    response = domain_module.app.test_client().post(
        "/domain",
        json={"owner": "BINGOik", "repo": "classifier", "api_key": "kimi-test"},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["result"] == "网页应用"
    assert domain_module.DomainClassifier.last_readme_text == "# GitHub Badge Extension"


def test_end_to_end_low_confidence_without_key_falls_back_to_svm(
    domain_module, fake_predictor_factory
):
    domain_module.fetch_readme = lambda owner, repo: "# Ambiguous Project"
    domain_module.extract_keywords_from_readme = lambda readme: "web extension api"
    domain_module.predictor = fake_predictor_factory([
        {"class": "应用插件", "prob": 0.50},
        {"class": "网页应用", "prob": 0.41},
    ])

    response = domain_module.app.test_client().post(
        "/domain",
        json={"owner": "sample", "repo": "ambiguous"},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["result"] == "应用插件"
    assert "warning" in data


def test_end_to_end_stops_when_feature_extraction_finds_no_keywords(
    domain_module, fake_predictor_factory
):
    class FailingPredictor:
        def predict_from_keyword(self, keywords):
            raise AssertionError("SVM should not run when keyword extraction is empty")

    domain_module.fetch_readme = lambda owner, repo: "the and of in"
    domain_module.extract_keywords_from_readme = lambda readme: ""
    domain_module.predictor = FailingPredictor()

    response = domain_module.app.test_client().post(
        "/domain",
        json={"owner": "sample", "repo": "empty"},
    )

    assert response.status_code == 200
    assert response.get_json()["result"] == ""


def test_end_to_end_returns_empty_when_svm_returns_no_candidates(
    domain_module, fake_predictor_factory
):
    domain_module.fetch_readme = lambda owner, repo: "# Unknown"
    domain_module.extract_keywords_from_readme = lambda readme: "unknown"
    domain_module.predictor = fake_predictor_factory([])

    response = domain_module.app.test_client().post(
        "/domain",
        json={"owner": "sample", "repo": "unknown"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["tags"] == "unknown"
    assert data["result"] == ""
    assert data["svm_result"] == []
    assert data["translated"] is False
