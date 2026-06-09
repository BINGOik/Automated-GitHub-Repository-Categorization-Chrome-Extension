import pytest


pytestmark = pytest.mark.unit


def test_gpt_extract_result_line_returns_value_after_result(gpt_predictor_module):
    assert (
        gpt_predictor_module.DomainClassifier.extract_result_line(
            "Result: 网页应用\nReasons: browser based UI"
        )
        == "网页应用"
    )


def test_gpt_extract_result_line_is_case_insensitive(gpt_predictor_module):
    assert gpt_predictor_module.DomainClassifier.extract_result_line("  result: 应用插件") == "应用插件"


def test_gpt_extract_result_line_returns_empty_for_missing_or_none_response(gpt_predictor_module):
    assert gpt_predictor_module.DomainClassifier.extract_result_line(None) == ""
    assert gpt_predictor_module.DomainClassifier.extract_result_line("Reasons only") == ""


def test_gpt_classify_builds_prediction_prompt_without_calling_network(gpt_predictor_module):
    captured = {}

    classifier = object.__new__(gpt_predictor_module.DomainClassifier)

    def fake_chat(messages, model="gpt-4o-mini"):
        captured["messages"] = messages
        captured["model"] = model
        return "Result: 代码开发工具或插件\nReasons: IDE extension."

    classifier.openai_sdk_chat_http_api = fake_chat

    result = classifier.classify(
        readme_text="A VS Code extension for developers.",
        prediction_dict={
            "Top1 Class": "应用插件",
            "Top1 Probability": 0.51,
            "Top2 Class": "代码开发工具或插件",
            "Top2 Probability": 0.46,
        },
    )

    assert result == "代码开发工具或插件"
    assert "Top1: 应用插件" in captured["messages"][0]["content"]
    assert "VS Code extension" in captured["messages"][0]["content"]


def test_kimi_classify_extracts_result_without_calling_network(kimi_predictor_module):
    captured = {}

    classifier = object.__new__(kimi_predictor_module.DomainClassifier)
    classifier.model = "moonshot-test"

    def fake_chat(messages, model=None):
        captured["messages"] = messages
        captured["model"] = model
        return "Result: 人工智能和机器学习应用\nReasons: ML model."

    classifier.openai_sdk_chat_http_api = fake_chat

    result = classifier.classify(
        readme_text="Train and serve machine learning models.",
        prediction_dict={
            "Top1 Class": "人工智能和机器学习应用",
            "Top1 Probability": 0.40,
        },
    )

    assert result == "人工智能和机器学习应用"
    assert captured["model"] == "moonshot-test"
    assert "Please only provide the Result:" in captured["messages"][0]["content"]


def test_kimi_translate_to_english_preserves_markdown_without_calling_network(
    kimi_predictor_module,
):
    captured = {}

    classifier = object.__new__(kimi_predictor_module.DomainClassifier)
    classifier.model = "moonshot-test"

    def fake_chat(messages, model=None):
        captured["messages"] = messages
        captured["model"] = model
        return "# OpenHarmony UI Kit\nA component library for HarmonyOS apps."

    classifier.openai_sdk_chat_http_api = fake_chat

    result = classifier.translate_to_english("# 鸿蒙组件库\n用于构建鸿蒙应用界面。")

    assert result == "# OpenHarmony UI Kit\nA component library for HarmonyOS apps."
    assert captured["model"] == "moonshot-test"
    assert "Translate the README to English" in captured["messages"][0]["content"]
    assert "Preserve Markdown structure" in captured["messages"][0]["content"]
