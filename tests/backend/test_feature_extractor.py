import pytest


pytestmark = pytest.mark.unit


def test_extract_keywords_returns_empty_for_blank_text(readme_words_module):
    assert readme_words_module.extract_keywords_from_readme("") == ""


def test_extract_keywords_lowercases_and_removes_common_stopwords(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "The React Project is a Web Application for Developers."
    )

    words = result.split()
    assert "react" in words
    assert "web" in words
    assert "application" in words
    assert "the" not in words
    assert "project" not in words


def test_extract_keywords_removes_fenced_code_blocks(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "Useful server API\n```python\nSECRET_TOKEN = 'abc'\n```"
    )

    assert "useful" in result.split()
    assert "server" in result.split()
    assert "secret" not in result
    assert "token" not in result


def test_extract_keywords_removes_inline_code(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "Install with `pip install package` and run the dashboard."
    )

    words = result.split()
    assert "dashboard" in words
    assert "pip" not in words
    assert "install" not in words


def test_extract_keywords_removes_urls_but_keeps_markdown_link_text(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "See [FastAPI docs](https://fastapi.tiangolo.com) or https://example.com now."
    )

    words = result.split()
    assert "fastapi" in words
    assert "docs" not in words  # "docs" is configured as a stopword.
    assert "https" not in words
    assert "example" not in words


def test_extract_keywords_respects_keep_top_k_by_frequency(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "react react react flask flask django",
        keep_top_k=2,
    )

    assert result.split() == ["react", "flask"]


def test_extract_keywords_filters_short_words_and_numbers_by_default(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "AI ML x 2024 123 server",
        min_len=3,
        keep_numbers=False,
    )

    assert result.split() == ["server"]


def test_extract_keywords_can_keep_numbers_when_enabled(readme_words_module):
    result = readme_words_module.extract_keywords_from_readme(
        "python 312 api 8000",
        keep_numbers=True,
        min_len=2,
    )

    words = result.split()
    assert "312" in words
    assert "8000" in words
    assert "python" in words
