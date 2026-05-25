"""Tests for POST /edit (Issue 7 — Edit + Save flow)."""
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_session(tmp_path: Path, sections: list[str] | None = None) -> tuple[str, Path]:
    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()

    sections = sections or ["readme"]

    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": "comprehensive"})
    )

    docs_dir = session_dir / "docs"
    docs_dir.mkdir()
    for key in sections:
        (docs_dir / f"{key}.md").write_text(f"# Original {key}\n\nOriginal content.")

    return session_id, session_dir


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: POST /edit returns 200
# ---------------------------------------------------------------------------


def test_edit_returns_200(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    response = client.post(
        "/edit",
        json={"session_id": session_id, "section": "readme", "content": "# Updated\n\nNew content."},
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Cycle 2 — content written to disk
# ---------------------------------------------------------------------------


def test_edit_persists_content_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme"])

    client.post(
        "/edit",
        json={"session_id": session_id, "section": "readme", "content": "# Updated\n\nNew content."},
    )

    saved = (session_dir / "docs" / "readme.md").read_text(encoding="utf-8")
    assert saved == "# Updated\n\nNew content."


# ---------------------------------------------------------------------------
# Cycle 3 — session.json records edited flag
# ---------------------------------------------------------------------------


def test_edit_sets_edited_flag_in_session(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme"])

    client.post(
        "/edit",
        json={"session_id": session_id, "section": "readme", "content": "# Updated"},
    )

    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session.get("edited", {}).get("readme") is True


# ---------------------------------------------------------------------------
# Cycle 4 — other section flags not touched
# ---------------------------------------------------------------------------


def test_edit_does_not_touch_other_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme", "api_reference"])

    client.post(
        "/edit",
        json={"session_id": session_id, "section": "readme", "content": "# Updated"},
    )

    # api_reference file is untouched
    other = (session_dir / "docs" / "api_reference.md").read_text(encoding="utf-8")
    assert "Original" in other

    # api_reference edited flag is absent
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert "api_reference" not in session.get("edited", {})


# ---------------------------------------------------------------------------
# Cycle 5 — 404 for unknown session
# ---------------------------------------------------------------------------


def test_edit_unknown_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    response = client.post(
        "/edit",
        json={"session_id": "does-not-exist", "section": "readme", "content": "# x"},
    )

    assert response.status_code == 404
