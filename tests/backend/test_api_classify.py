import pytest


pytestmark = pytest.mark.unit


def test_domain_requires_owner_repo_or_repo_url(domain_module):
    client = domain_module.app.test_client()

    response = client.post("/domain", json={})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_domain_returns_svm_result_when_confidence_gap_is_high(domain_module, fake_predictor_factory):
    domain_module.fetch_readme = lambda owner, repo: "# React\nA web UI library."
    domain_module.extract_keywords_from_readme = lambda text: "react web ui"
    domain_module.predictor = fake_predictor_factory([
        {"class": "网页应用", "prob": 0.87},
        {"class": "代码开发工具或插件", "prob": 0.09},
    ])
    client = domain_module.app.test_client()

    response = client.post("/domain", json={"owner": "facebook", "repo": "react"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["tags"] == "react web ui"
    assert data["result"] == "网页应用"
    assert data["svm_result"][0]["prob"] == 0.87


def test_domain_accepts_repo_url_and_extracts_owner_repo(domain_module, fake_predictor_factory):
    seen = {}

    def fake_fetch_readme(owner, repo):
        seen["owner"] = owner
        seen["repo"] = repo
        return "# Flask API"

    domain_module.fetch_readme = fake_fetch_readme
    domain_module.extract_keywords_from_readme = lambda text: "flask api"
    domain_module.predictor = fake_predictor_factory()
    client = domain_module.app.test_client()

    response = client.post(
        "/domain",
        json={"repo_url": "https://github.com/pallets/flask"},
    )

    assert response.status_code == 200
    assert seen == {"owner": "pallets", "repo": "flask"}


def test_domain_returns_500_when_readme_fetch_fails(domain_module):
    domain_module.fetch_readme = lambda owner, repo: (_ for _ in ()).throw(
        RuntimeError("README not found")
    )
    client = domain_module.app.test_client()

    response = client.post("/domain", json={"owner": "x", "repo": "missing"})

    assert response.status_code == 500
    assert "README not found" in response.get_json()["error"]


def test_domain_returns_empty_result_when_no_keywords(domain_module, fake_predictor_factory):
    domain_module.fetch_readme = lambda owner, repo: ""
    domain_module.extract_keywords_from_readme = lambda text: ""
    domain_module.predictor = fake_predictor_factory(exc=AssertionError("must not call SVM"))
    client = domain_module.app.test_client()

    response = client.post("/domain", json={"owner": "x", "repo": "empty"})

    assert response.status_code == 200
    assert response.get_json() == {"tags": "", "result": "", "svm_result": []}


def test_domain_returns_500_when_svm_prediction_fails(domain_module, fake_predictor_factory):
    domain_module.fetch_readme = lambda owner, repo: "# README"
    domain_module.extract_keywords_from_readme = lambda text: "python flask"
    domain_module.predictor = fake_predictor_factory(exc=ValueError("bad model"))
    client = domain_module.app.test_client()

    response = client.post("/domain", json={"owner": "x", "repo": "bad-model"})

    assert response.status_code == 500
    assert "SVM预测失败" in response.get_json()["error"]


def test_domain_falls_back_to_svm_when_low_confidence_and_no_api_key(
    domain_module, fake_predictor_factory
):
    domain_module.fetch_readme = lambda owner, repo: "# Ambiguous"
    domain_module.extract_keywords_from_readme = lambda text: "extension web api"
    domain_module.predictor = fake_predictor_factory([
        {"class": "应用插件", "prob": 0.51},
        {"class": "网页应用", "prob": 0.44},
    ])
    client = domain_module.app.test_client()

    response = client.post("/domain", json={"owner": "x", "repo": "ambiguous"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["result"] == "应用插件"
    assert "warning" in data


def test_domain_uses_llm_refiner_when_low_confidence_and_api_key(
    domain_module, fake_predictor_factory
):
    domain_module.fetch_readme = lambda owner, repo: "# Chrome Extension\nAdds badges to GitHub."
    domain_module.extract_keywords_from_readme = lambda text: "chrome extension badges"
    domain_module.predictor = fake_predictor_factory([
        {"class": "应用插件", "prob": 0.50},
        {"class": "代码开发工具或插件", "prob": 0.42},
    ])
    client = domain_module.app.test_client()

    response = client.post(
        "/domain",
        json={"owner": "BINGOik", "repo": "classifier", "api_key": "test-key"},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["result"] == "网页应用"
    assert domain_module.DomainClassifier.last_api_key == "test-key"
    assert domain_module.DomainClassifier.last_prediction_dict["Top1 Class"] == "应用插件"
