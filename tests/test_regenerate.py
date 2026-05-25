"""Tests for GET /regenerate/{session_id}/{section_key} (Issue 8)."""
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_session(
    tmp_path: Path,
    sections: list[str] | None = None,
    edited: dict | None = None,
) -> tuple[str, Path]:
    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()

    sections = sections or ["readme"]

    sess: dict = {"session_id": session_id, "mode": "comprehensive"}
    if edited:
        sess["edited"] = edited
    (session_dir / "session.json").write_text(json.dumps(sess))

    docs_dir = session_dir / "docs"
    docs_dir.mkdir()
    for key in sections:
        (docs_dir / f"{key}.md").write_text(f"# Original {key}\n\nOriginal content.")

    mapping = {
        "readme": ["README.md"],
        "api_reference": ["main.py"],
        "architecture": "root/\n  main.py",
        "getting_started": ["requirements.txt"],
        "deployment": [],
    }
    (session_dir / "mapping.json").write_text(json.dumps(mapping))

    return session_id, session_dir


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: endpoint returns 200 text/event-stream
# ---------------------------------------------------------------------------


def test_regenerate_returns_200_event_stream(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    async def _fake_stream(system, prompt):
        yield "Hello"
        yield " world"

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    response = client.get(f"/regenerate/{session_id}/readme")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Cycle 2 — tokens arrive as unnamed SSE data lines
# ---------------------------------------------------------------------------


def test_regenerate_streams_tokens_as_data_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    async def _fake_stream(system, prompt):
        yield "Hello"
        yield " world"

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    response = client.get(f"/regenerate/{session_id}/readme")
    body = response.text

    assert 'data: "Hello"\n' in body
    assert 'data: " world"\n' in body


# ---------------------------------------------------------------------------
# Cycle 3 — named 'done' event sent at end
# ---------------------------------------------------------------------------


def test_regenerate_sends_done_event(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path, ["readme"])

    async def _fake_stream(system, prompt):
        yield "token"

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    response = client.get(f"/regenerate/{session_id}/readme")

    assert "event: done" in response.text


# ---------------------------------------------------------------------------
# Cycle 4 — new content written to docs/<section>.md
# ---------------------------------------------------------------------------


def test_regenerate_writes_new_content_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme"])

    async def _fake_stream(system, prompt):
        yield "# New README\n"
        yield "\nFresh content."

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    client.get(f"/regenerate/{session_id}/readme")

    saved = (session_dir / "docs" / "readme.md").read_text(encoding="utf-8")
    assert saved == "# New README\n\nFresh content."


# ---------------------------------------------------------------------------
# Cycle 5 — edited flag cleared after regeneration
# ---------------------------------------------------------------------------


def test_regenerate_clears_edited_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(
        tmp_path, ["readme"], edited={"readme": True}
    )

    async def _fake_stream(system, prompt):
        yield "token"

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    client.get(f"/regenerate/{session_id}/readme")

    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    assert session.get("edited", {}).get("readme") is not True


# ---------------------------------------------------------------------------
# Cycle 6 — other sections untouched
# ---------------------------------------------------------------------------


def test_regenerate_does_not_alter_other_sections(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, session_dir = _make_session(tmp_path, ["readme", "api_reference"])

    async def _fake_stream(system, prompt):
        yield "new readme content"

    monkeypatch.setattr("generator._stream_section", _fake_stream)

    client.get(f"/regenerate/{session_id}/readme")

    other = (session_dir / "docs" / "api_reference.md").read_text(encoding="utf-8")
    assert "Original" in other


# ---------------------------------------------------------------------------
# Cycle 7 — 404 for unknown session
# ---------------------------------------------------------------------------


def test_regenerate_unknown_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    response = client.get("/regenerate/does-not-exist/readme")

    assert response.status_code == 404
