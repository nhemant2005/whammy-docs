"""Tests for GET /generate/<session_id> and GET /stream/<session_id> (Issue 4)."""
import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_session(tmp_path: Path, mapping: dict = None) -> tuple[str, Path]:
    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": "quick"})
    )
    (session_dir / "mapping.json").write_text(
        json.dumps(
            mapping
            or {
                "readme": [],
                "api_reference": [],
                "getting_started": [],
                "deployment": [],
                "architecture": "",
            }
        )
    )
    return session_id, session_dir


async def _fake_stream(session_dir):
    yield "Hello"
    yield " world"


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: SSE content-type
# ---------------------------------------------------------------------------


def test_stream_endpoint_returns_event_stream_content_type(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    with patch("main.stream_readme", _fake_stream):
        response = client.get(f"/stream/{session_id}")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Cycle 2 — tokens arrive wrapped in SSE data: lines
# ---------------------------------------------------------------------------


def test_stream_response_wraps_tokens_as_data_events(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    with patch("main.stream_readme", _fake_stream):
        response = client.get(f"/stream/{session_id}")

    lines = [l for l in response.text.splitlines() if l.strip()]
    data_lines = [l for l in lines if l.startswith("data:")]
    assert len(data_lines) >= 2


# ---------------------------------------------------------------------------
# Cycle 3 — generate page serves HTML
# ---------------------------------------------------------------------------


def test_generate_page_returns_html(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    response = client.get(f"/generate/{session_id}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Cycle 4 — generate page wires up HTMX SSE extension
# ---------------------------------------------------------------------------


def test_generate_page_includes_sse_connect_for_session(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    response = client.get(f"/generate/{session_id}")

    assert f"/stream/{session_id}" in response.text
    assert "sse-connect" in response.text


# ---------------------------------------------------------------------------
# Cycle 5 — unknown session returns 404
# ---------------------------------------------------------------------------


def test_stream_unknown_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    response = client.get("/stream/does-not-exist")

    assert response.status_code == 404
