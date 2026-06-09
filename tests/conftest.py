"""Shared pytest helpers for the GitHub Repository Domain Classifier tests.

The backend entrypoint imports the SVM predictor at module import time.  These
fixtures replace network/model/LLM dependencies with stubs so the suite can run
locally and in CI without real tokens, pickle models, or API calls.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
EXTENSION_DIR = PROJECT_ROOT / "extension"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


def load_module_from_file(module_name: str, file_path: Path):
    """Load a Python file by path under a temporary module name."""
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class StubPredictor:
    """Default SVM predictor used while importing domain_get.py."""

    def __init__(self, *args, **kwargs):
        self.result = [
            {"class": "网页应用", "prob": 0.90},
            {"class": "代码开发工具或插件", "prob": 0.05},
        ]

    def predict_from_keyword(self, keywords: str):
        return list(self.result)


class StubDomainClassifier:
    """Default LLM refiner used while importing domain_get.py."""

    last_api_key = None
    last_readme_text = None
    last_prediction_dict = None
    last_translation_text = None

    def __init__(self, api_key: str):
        type(self).last_api_key = api_key
        self.api_key = api_key

    def translate_to_english(self, readme_text: str) -> str:
        type(self).last_translation_text = readme_text
        return "# OpenHarmony UI Kit\nA component library for HarmonyOS applications."

    def classify(self, readme_text: str, prediction_dict: dict):
        type(self).last_readme_text = readme_text
        type(self).last_prediction_dict = dict(prediction_dict)
        return "网页应用"


@pytest.fixture(autouse=True)
def add_backend_to_path(monkeypatch):
    monkeypatch.syspath_prepend(str(BACKEND_DIR))


@pytest.fixture()
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture()
def backend_dir() -> Path:
    return BACKEND_DIR


@pytest.fixture()
def extension_dir() -> Path:
    return EXTENSION_DIR


@pytest.fixture()
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture()
def readme_words_module():
    return load_module_from_file("readme_words_under_test", BACKEND_DIR / "readme_words.py")


@pytest.fixture()
def svm_predictor_module():
    return load_module_from_file("svm_predictor_under_test", BACKEND_DIR / "svm_predictor.py")


@pytest.fixture()
def gpt_predictor_module():
    return load_module_from_file("gpt_predictor_under_test", BACKEND_DIR / "gpt_predictor.py")


@pytest.fixture()
def kimi_predictor_module():
    return load_module_from_file("kimi_predictor_under_test", BACKEND_DIR / "kimi_predictor.py")


@pytest.fixture()
def domain_module(monkeypatch):
    """Import domain_get.py with heavy dependencies stubbed out."""
    fake_svm_module = types.ModuleType("svm_predictor")
    fake_svm_module.Predictor = StubPredictor

    fake_readme_module = types.ModuleType("readme_words")
    fake_readme_module.extract_keywords_from_readme = (
        lambda text: "flask react api web" if text else ""
    )

    fake_kimi_module = types.ModuleType("kimi_predictor")
    fake_kimi_module.DomainClassifier = StubDomainClassifier

    monkeypatch.setitem(sys.modules, "svm_predictor", fake_svm_module)
    monkeypatch.setitem(sys.modules, "readme_words", fake_readme_module)
    monkeypatch.setitem(sys.modules, "kimi_predictor", fake_kimi_module)

    module = load_module_from_file("domain_get_under_test", BACKEND_DIR / "domain_get.py")
    module.app.config.update(TESTING=True)
    return module


class FakePredictor:
    def __init__(self, result=None, exc: Exception | None = None):
        self.result = result if result is not None else [
            {"class": "网页应用", "prob": 0.90},
            {"class": "代码开发工具或插件", "prob": 0.05},
        ]
        self.exc = exc
        self.called_with = None

    def predict_from_keyword(self, keywords: str):
        self.called_with = keywords
        if self.exc:
            raise self.exc
        return list(self.result)


@pytest.fixture()
def fake_predictor_factory():
    return FakePredictor
