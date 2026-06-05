import base64

import pytest


pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, *, ok, text="", status_code=200, payload=None):
        self.ok = ok
        self.text = text
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_fetch_readme_requires_github_token(domain_module):
    domain_module.GITHUB_TOKEN = ""

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        domain_module.fetch_readme("owner", "repo")


def test_fetch_readme_returns_raw_readme_when_primary_endpoint_succeeds(
    domain_module, monkeypatch
):
    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return FakeResponse(ok=True, text="# Raw README", status_code=200)

    monkeypatch.setattr(domain_module.requests, "get", fake_get)
    domain_module.GITHUB_TOKEN = "ghp_test"

    readme = domain_module.fetch_readme("owner", "repo")

    assert readme == "# Raw README"
    assert calls[0][0] == "https://api.github.com/repos/owner/repo/readme"
    assert calls[0][1]["Accept"] == "application/vnd.github.v3.raw"
    assert calls[0][2] == 15


def test_fetch_readme_falls_back_to_contents_endpoint_and_decodes_base64(
    domain_module, monkeypatch
):
    encoded = base64.b64encode("# Fallback README".encode()).decode()
    responses = [
        FakeResponse(ok=False, text="not found", status_code=404),
        FakeResponse(ok=True, payload={"content": encoded}, status_code=200),
    ]

    monkeypatch.setattr(domain_module.requests, "get", lambda *args, **kwargs: responses.pop(0))
    domain_module.GITHUB_TOKEN = "ghp_test"

    readme = domain_module.fetch_readme("owner", "repo")

    assert readme == "# Fallback README"


def test_fetch_readme_uses_json_accept_header_for_fallback(domain_module, monkeypatch):
    seen_headers = []

    def fake_get(url, headers, timeout):
        seen_headers.append(dict(headers))
        if len(seen_headers) == 1:
            return FakeResponse(ok=False, text="not found", status_code=404)
        return FakeResponse(
            ok=True,
            payload={"content": base64.b64encode(b"# README").decode()},
            status_code=200,
        )

    monkeypatch.setattr(domain_module.requests, "get", fake_get)
    domain_module.GITHUB_TOKEN = "ghp_test"

    domain_module.fetch_readme("owner", "repo")

    assert seen_headers[0]["Accept"] == "application/vnd.github.v3.raw"
    assert seen_headers[1]["Accept"] == "application/vnd.github+json"


def test_fetch_readme_raises_when_fallback_has_no_content(domain_module, monkeypatch):
    responses = [
        FakeResponse(ok=False, text="not found", status_code=404),
        FakeResponse(ok=True, payload={}, text="{}", status_code=200),
    ]

    monkeypatch.setattr(domain_module.requests, "get", lambda *args, **kwargs: responses.pop(0))
    domain_module.GITHUB_TOKEN = "ghp_test"

    with pytest.raises(RuntimeError, match="README 获取失败"):
        domain_module.fetch_readme("owner", "repo")


def test_fetch_readme_error_includes_primary_and_fallback_statuses(domain_module, monkeypatch):
    responses = [
        FakeResponse(ok=False, text="primary missing", status_code=404),
        FakeResponse(ok=False, text="fallback forbidden", status_code=403),
    ]

    monkeypatch.setattr(domain_module.requests, "get", lambda *args, **kwargs: responses.pop(0))
    domain_module.GITHUB_TOKEN = "ghp_test"

    with pytest.raises(RuntimeError) as exc:
        domain_module.fetch_readme("owner", "repo")

    message = str(exc.value)
    assert "/readme=404" in message
    assert "/contents=403" in message
