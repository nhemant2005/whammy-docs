"""Tests for Issue 5 — full generation pipeline (multi-section, skeleton, SSE events)."""
import json
import uuid
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from generator import _skeleton

client = TestClient(app)


def _make_session(tmp_path: Path, mode: str = "comprehensive") -> tuple[str, Path]:
    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": mode})
    )
    (session_dir / "mapping.json").write_text(
        json.dumps(
            {
                "readme": [],
                "api_reference": [],
                "getting_started": [],
                "deployment": [],
                "architecture": "",
            }
        )
    )
    return session_id, session_dir


# ---------------------------------------------------------------------------
# Skeleton extraction
# ---------------------------------------------------------------------------


def test_skeleton_small_file_returns_full_content():
    text = "x" * 4000  # < 5 KB
    assert _skeleton(text, "foo.py") == text


def test_skeleton_large_file_returns_first_30_lines():
    lines = [f"line {i}" for i in range(100)]
    text = "\n".join(lines)
    # Pad to > 20 KB
    padding = "a" * (21 * 1024)
    large_text = padding + "\n" + text
    result = _skeleton(large_text, "foo.py")
    assert len(result.splitlines()) <= 30


def test_skeleton_medium_file_python_returns_signatures():
    body = "\n".join(
        [
            "import os",
            "",
            "def foo():",
            '    """Foo docstring."""',
            "    return 1",
            "",
            "class Bar:",
            '    """Bar class."""',
            "    pass",
        ]
    )
    # Pad to 6 KB (medium range 5–20 KB)
    padding = "# comment\n" * 600  # ~6 KB
    medium_text = padding + body
    result = _skeleton(medium_text, "module.py")
    assert "def foo" in result
    assert "class Bar" in result


# ---------------------------------------------------------------------------
# stream_all_sections — mode routing
# ---------------------------------------------------------------------------


async def _fake_section_stream(session_dir):
    """Minimal fake that yields one section-start per section then done."""
    from generator import _QUICK_SECTIONS, _COMPREHENSIVE_SECTIONS
    session = json.loads((session_dir / "session.json").read_text())
    mode = session.get("mode", "comprehensive")
    sections = _QUICK_SECTIONS if mode == "quick" else _COMPREHENSIVE_SECTIONS
    for key in sections:
        yield ("section-start", key)
        yield ("section-complete", key)
    yield ("done", "")


@pytest.mark.asyncio
async def test_comprehensive_mode_generates_five_sections(tmp_path):
    from generator import stream_all_sections
    _, session_dir = _make_session(tmp_path, mode="comprehensive")

    with patch("generator._stream_section", return_value=_empty_async_iter()):
        events = [(t, d) async for t, d in stream_all_sections(session_dir)]

    starts = [d for t, d in events if t == "section-start"]
    assert len(starts) == 5


@pytest.mark.asyncio
async def test_quick_mode_generates_two_sections(tmp_path):
    from generator import stream_all_sections
    _, session_dir = _make_session(tmp_path, mode="quick")

    with patch("generator._stream_section", return_value=_empty_async_iter()):
        events = [(t, d) async for t, d in stream_all_sections(session_dir)]

    starts = [d for t, d in events if t == "section-start"]
    assert len(starts) == 2


@pytest.mark.asyncio
async def test_done_event_fires_last(tmp_path):
    from generator import stream_all_sections
    _, session_dir = _make_session(tmp_path, mode="quick")

    with patch("generator._stream_section", return_value=_empty_async_iter()):
        events = [(t, d) async for t, d in stream_all_sections(session_dir)]

    assert events[-1][0] == "done"


async def _empty_async_iter():
    return
    yield  # make it an async generator


# ---------------------------------------------------------------------------
# Stream endpoint — named SSE events
# ---------------------------------------------------------------------------


async def _fake_all_sections(session_dir):
    yield ("section-start", "readme")
    yield ("message", "Hello world")
    yield ("section-complete", "readme")
    yield ("done", "")


def test_stream_endpoint_emits_named_section_start_event(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    with patch("main.stream_all_sections", _fake_all_sections):
        response = client.get(f"/stream/{session_id}")

    assert "event: section-start" in response.text


def test_stream_endpoint_emits_named_done_event(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    with patch("main.stream_all_sections", _fake_all_sections):
        response = client.get(f"/stream/{session_id}")

    assert "event: done" in response.text


def test_stream_endpoint_emits_message_token_as_data_only(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    session_id, _ = _make_session(tmp_path)

    with patch("main.stream_all_sections", _fake_all_sections):
        response = client.get(f"/stream/{session_id}")

    lines = response.text.splitlines()
    data_lines = [l for l in lines if l.startswith("data:")]
    # "Hello world" token should appear as a plain data: line
    assert any("Hello world" in l for l in data_lines)
