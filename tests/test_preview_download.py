"""Tests for GET /preview/<session_id> and GET /download/<session_id> (Issue 6)."""
import io
import json
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_SECTION_TITLES = {
    "readme": "README",
    "api_reference": "API Reference",
    "architecture": "Architecture",
    "getting_started": "Getting Started",
    "deployment": "Deployment",
}


def _make_session(tmp_path: Path, sections: list[str] | None = None) -> tuple[str, Path]:
    """Create a session directory with generated doc files."""
    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()

    sections = sections or ["readme"]

    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": "comprehensive"})
    )
    (session_dir / "mapping.json").write_text(
        json.dumps({
            "readme": [],
            "api_reference": [],
            "getting_started": [],
            "deployment": [],
            "architecture": "",
        })
    )

    docs_dir = session_dir / "docs"
    docs_dir.mkdir()
    for key in sections:
        title = _SECTION_TITLES.get(key, key)
        (docs_dir / f"{key}.md").write_text(f"# {title}\n\nContent here.")

    return session_id, session_dir


def _make_site(session_dir: Path) -> None:
    """Fake a mkdocs build by creating a minimal site/ directory."""
    site_dir = session_dir / "site"
    site_dir.mkdir(exist_ok=True)
    (site_dir / "index.html").write_text("<html><body>Docs</body></html>")


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: preview page returns HTML
# ---------------------------------------------------------------------------


def test_preview_page_returns_html(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    response = client.get(f"/preview/{session_id}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Cycle 2 — section cards have stable HTML IDs
# ---------------------------------------------------------------------------


def test_preview_page_has_section_card_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme", "api_reference"])

    response = client.get(f"/preview/{session_id}")

    assert 'id="section-readme"' in response.text
    assert 'id="section-api-reference"' in response.text


# ---------------------------------------------------------------------------
# Cycle 3 — page includes marked.js for markdown rendering
# ---------------------------------------------------------------------------


def test_preview_page_includes_marked_js(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    response = client.get(f"/preview/{session_id}")

    assert "marked" in response.text


# ---------------------------------------------------------------------------
# Cycle 4 — section cards have Edit and Regenerate buttons
# ---------------------------------------------------------------------------


def test_preview_page_has_edit_and_regenerate_buttons(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    response = client.get(f"/preview/{session_id}")

    assert "Edit" in response.text
    assert "Regenerate" in response.text


# ---------------------------------------------------------------------------
# Cycle 5 — 404 for unknown session
# ---------------------------------------------------------------------------


def test_preview_unknown_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    response = client.get("/preview/does-not-exist")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Cycle 6 — download returns a zip attachment
# ---------------------------------------------------------------------------


def test_download_returns_zip(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme"])
    _make_site(session_dir)

    with patch("subprocess.run"):
        response = client.get(f"/download/{session_id}")

    assert response.status_code == 200
    assert "zip" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Cycle 7 — zip contains markdown source files
# ---------------------------------------------------------------------------


def test_download_zip_contains_markdown_files(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme", "api_reference"])
    _make_site(session_dir)

    with patch("subprocess.run"):
        response = client.get(f"/download/{session_id}")

    assert response.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert any(name.endswith(".md") for name in names)


# ---------------------------------------------------------------------------
# Cycle 8 — download 404 for unknown session
# ---------------------------------------------------------------------------


def test_download_unknown_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    response = client.get("/download/does-not-exist")

    assert response.status_code == 404
