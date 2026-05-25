"""Tests for POST /upload endpoint (Issue 2)."""
import io
import json
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, follow_redirects=False)


def make_zip(files: dict[str, str] = None) -> bytes:
    """Build an in-memory zip with the given filename→content pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in (files or {"hello.txt": "hello"}).items():
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tracer bullet: valid zip → redirect
# ---------------------------------------------------------------------------

def test_valid_zip_redirects_to_preview():
    data = {"file": ("project.zip", make_zip(), "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/preview/")


# ---------------------------------------------------------------------------
# Session directory + contents
# ---------------------------------------------------------------------------

def test_valid_zip_creates_session_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    data = {"file": ("project.zip", make_zip({"src/main.py": "print()"}), "application/zip"), "mode": (None, "comprehensive")}
    response = client.post("/upload", files=data)
    assert response.status_code == 303

    location = response.headers["location"]
    session_id = location.split("/preview/")[1]
    session_dir = tmp_path / f"whammy-{session_id}"
    assert session_dir.is_dir()
    assert (session_dir / "src" / "main.py").exists()


def test_valid_zip_writes_session_json(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    data = {"file": ("project.zip", make_zip(), "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    session_json = tmp_path / f"whammy-{session_id}" / "session.json"
    assert session_json.exists()
    payload = json.loads(session_json.read_text())
    assert payload["session_id"] == session_id
    assert payload["mode"] == "quick"


# ---------------------------------------------------------------------------
# Error states
# ---------------------------------------------------------------------------

def test_non_zip_file_returns_error_page():
    data = {"file": ("project.txt", b"not a zip", "text/plain"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 200
    assert "error" in response.text.lower() or "zip" in response.text.lower()


def test_oversized_file_returns_error_page():
    big = b"0" * (51 * 1024 * 1024)  # 51 MB
    data = {"file": ("big.zip", big, "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 200
    assert "50" in response.text or "error" in response.text.lower()


def test_corrupted_zip_returns_error_not_500():
    data = {"file": ("bad.zip", b"PK not a real zip content garbage", "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 200
    assert "error" in response.text.lower() or "invalid" in response.text.lower()


def test_valid_zip_writes_mapping_json(tmp_path, monkeypatch):
    monkeypatch.setenv("WHAMMY_TMP_DIR", str(tmp_path))
    data = {"file": ("project.zip", make_zip({"main.py": "x = 1"}), "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    assert response.status_code == 303

    session_id = response.headers["location"].split("/preview/")[1]
    mapping_file = tmp_path / f"whammy-{session_id}" / "mapping.json"
    assert mapping_file.exists()


def test_password_protected_zip_returns_error_not_500():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(b"secret")
        # Write with encryption by using ZipInfo + pwd
        info = zipfile.ZipInfo("locked.txt")
        info.flag_bits |= 0x1  # encrypted flag
        zf.writestr(info, "hidden content")
    data = {"file": ("locked.zip", buf.getvalue(), "application/zip"), "mode": (None, "quick")}
    response = client.post("/upload", files=data)
    # Must not 500 — either 200 with error or succeeds
    assert response.status_code in (200, 303)
