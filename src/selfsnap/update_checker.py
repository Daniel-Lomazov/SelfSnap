from __future__ import annotations

import json
import urllib.error
import urllib.request

_GITHUB_RELEASES_URL = "https://api.github.com/repos/{repo}/releases/latest"


def fetch_latest_release_tag(repo: str) -> str | None:
    """Return the latest release tag from GitHub (e.g. ``"v0.9.4"``), or ``None`` on any error."""
    url = _GITHUB_RELEASES_URL.format(repo=repo)
    req = urllib.request.Request(url, headers={"User-Agent": "SelfSnap-update-checker/1"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data: dict = json.loads(resp.read().decode())
            tag = data.get("tag_name") or ""
            return tag.strip() or None
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None


def compare_versions(current: str, other: str) -> int:
    """Compare two version strings (with or without a leading ``v``).

    Returns:
        negative  if ``current`` is older than ``other``
        0         if equal
        positive  if ``current`` is newer than ``other``
    """

    def _parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.lstrip("v").split("."))

    a, b = _parse(current), _parse(other)
    return (a > b) - (a < b)
