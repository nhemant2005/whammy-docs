"""Tests for static file serving: theme.css, Unageo font, and template DOM IDs."""
import json
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_theme_css_served():
    r = client.get("/static/css/theme.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["content-type"]


def test_unageo_regular_served():
    r = client.get("/static/unageo/ttf/Unageo-Regular.ttf")
    assert r.status_code == 200


def test_gradient_layer_present_in_preview(tmp_path, monkeypatch):
    """gradient-layer div must be in preview.html (both generating and done states)."""
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))

    session_id = str(uuid.uuid4())
    session_dir = tmp_path / f"whammy-{session_id}"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": "quick"})
    )
    (session_dir / "mapping.json").write_text(json.dumps({"readme": [], "api_reference": []}))

    # Generating state (no docs yet)
    r = client.get(f"/preview/{session_id}")
    assert r.status_code == 200
    assert 'id="gradient-layer"' in r.text

    # Done state (docs present)
    docs_dir = session_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "readme.md").write_text("# Hello")
    r2 = client.get(f"/preview/{session_id}")
    assert r2.status_code == 200
    assert 'id="gradient-layer"' in r2.text
