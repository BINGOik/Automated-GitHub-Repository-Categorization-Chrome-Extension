import json

import pytest


pytestmark = pytest.mark.extension


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def test_manifest_uses_manifest_v3(extension_dir):
    manifest = json.loads(read_text(extension_dir / "manifest.json"))

    assert manifest["manifest_version"] == 3
    assert manifest["name"] == "GitHub README Domain Classifier"


def test_manifest_declares_storage_permission(extension_dir):
    manifest = json.loads(read_text(extension_dir / "manifest.json"))

    assert "storage" in manifest["permissions"]


def test_manifest_allows_github_and_local_backend(extension_dir):
    manifest = json.loads(read_text(extension_dir / "manifest.json"))

    assert "https://github.com/*" in manifest["host_permissions"]
    assert "http://127.0.0.1:8000/*" in manifest["host_permissions"]


def test_manifest_registers_content_script_for_github(extension_dir):
    manifest = json.loads(read_text(extension_dir / "manifest.json"))
    script = manifest["content_scripts"][0]

    assert script["matches"] == ["https://github.com/*"]
    assert script["js"] == ["content.js"]
    assert script["run_at"] == "document_idle"


def test_content_script_posts_to_domain_backend(extension_dir):
    source = read_text(extension_dir / "content.js")

    assert 'const API_URL = "http://127.0.0.1:8000/domain"' in source
    assert 'method: "POST"' in source
    assert '"Content-Type": "application/json"' in source


def test_content_parser_requires_exact_owner_repo_path(extension_dir):
    source = read_text(extension_dir / "content.js")

    assert "function parseOwnerRepoFromHref" in source
    assert "parts.length !== 2" in source


def test_content_script_limits_concurrency_and_uses_session_cache(extension_dir):
    source = read_text(extension_dir / "content.js")

    assert "const MAX_CONCURRENCY = 3" in source
    assert "sessionStorage.getItem" in source
    assert "sessionStorage.setItem" in source


def test_popup_reads_and_saves_extension_settings(extension_dir):
    source = read_text(extension_dir / "popup.js")

    assert "dc_enabled" in source
    assert "dc_openai_key" in source
    assert "dc_github_token" in source
    assert "chrome.storage.local.get" in source
    assert "chrome.storage.local.set" in source
