"""Tests for POST /upload-sample (Issue 9)."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# Cycle 1 — tracer bullet: POST /upload-sample → 303 redirect to /generate/
# ---------------------------------------------------------------------------


def test_upload_sample_redirects_to_preview(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    response = client.post("/upload-sample")
    assert response.status_code == 303
    assert response.headers["location"].startswith("/preview/")


# ---------------------------------------------------------------------------
# Cycle 2 — session directory created in tmp
# ---------------------------------------------------------------------------


def test_upload_sample_creates_session_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    response = client.post("/upload-sample")
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    session_dir = tmp_path / f"whammy-{session_id}"
    assert session_dir.is_dir()


# ---------------------------------------------------------------------------
# Cycle 3 — session.json has mode=comprehensive and project_name=todo-app
# ---------------------------------------------------------------------------


def test_upload_sample_session_json_values(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    response = client.post("/upload-sample")
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    session_json = tmp_path / f"whammy-{session_id}" / "session.json"
    assert session_json.exists()

    payload = json.loads(session_json.read_text())
    assert payload["mode"] == "comprehensive"
    assert payload["project_name"] == "todo-app"
    assert payload["session_id"] == session_id


# ---------------------------------------------------------------------------
# Cycle 4 — mapping.json exists (scan() was called)
# ---------------------------------------------------------------------------


def test_upload_sample_creates_mapping_json(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    response = client.post("/upload-sample")
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    mapping = tmp_path / f"whammy-{session_id}" / "mapping.json"
    assert mapping.exists()


# ---------------------------------------------------------------------------
# Cycle 5 — sample source files are present in the session directory
# ---------------------------------------------------------------------------


def test_upload_sample_extracts_sample_files(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    response = client.post("/upload-sample")
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    session_dir = tmp_path / f"whammy-{session_id}"
    py_files = list(session_dir.rglob("*.py"))
    assert len(py_files) >= 1, "Expected at least one .py file from the sample project"
