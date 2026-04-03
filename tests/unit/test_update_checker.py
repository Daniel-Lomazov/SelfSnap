from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from selfsnap.update_checker import compare_versions, fetch_latest_release_tag

# ---------------------------------------------------------------------------
# compare_versions
# ---------------------------------------------------------------------------


def test_compare_versions_equal() -> None:
    assert compare_versions("0.9.3", "v0.9.3") == 0


def test_compare_versions_current_older() -> None:
    assert compare_versions("0.9.3", "v0.9.4") < 0


def test_compare_versions_current_newer() -> None:
    assert compare_versions("0.9.5", "v0.9.3") > 0


def test_compare_versions_strips_leading_v() -> None:
    assert compare_versions("v1.0.0", "1.0.0") == 0


def test_compare_versions_major_bump() -> None:
    assert compare_versions("0.9.3", "1.0.0") < 0


# ---------------------------------------------------------------------------
# fetch_latest_release_tag
# ---------------------------------------------------------------------------


def _mock_response(tag_name: str, status: int = 200) -> MagicMock:
    body = json.dumps({"tag_name": tag_name}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_latest_release_tag_returns_tag(monkeypatch) -> None:
    mock_resp = _mock_response("v0.9.4")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_latest_release_tag("owner/repo")
    assert result == "v0.9.4"


def test_fetch_latest_release_tag_strips_whitespace(monkeypatch) -> None:
    mock_resp = _mock_response("  v0.9.4  ")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_latest_release_tag("owner/repo")
    assert result == "v0.9.4"


def test_fetch_latest_release_tag_returns_none_on_network_error() -> None:
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = fetch_latest_release_tag("owner/repo")
    assert result is None


def test_fetch_latest_release_tag_returns_none_on_bad_json() -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not json"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_latest_release_tag("owner/repo")
    assert result is None


def test_fetch_latest_release_tag_returns_none_on_missing_key() -> None:
    body = json.dumps({"name": "Release"}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = fetch_latest_release_tag("owner/repo")
    assert result is None
