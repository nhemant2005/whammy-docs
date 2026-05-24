"""Tests for scanner.py (Issue 3) — file scanner + section→file mapping."""
import json
from pathlib import Path

import pytest

from scanner import scan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_project(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    """Write files into tmp_path and return tmp_path."""
    for rel, content in files.items():
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            dest.write_bytes(content)
        else:
            dest.write_text(content, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Tracer bullet: scan() returns mapping with all expected section keys
# ---------------------------------------------------------------------------

def test_scan_returns_all_section_keys(tmp_path):
    make_project(tmp_path, {"main.py": "print('hello')"})
    result = scan(tmp_path)
    assert set(result.keys()) >= {"api_reference", "getting_started", "deployment", "architecture", "readme"}


# ---------------------------------------------------------------------------
# mapping.json is written to session folder
# ---------------------------------------------------------------------------

def test_scan_writes_mapping_json(tmp_path):
    make_project(tmp_path, {"main.py": "x = 1"})
    scan(tmp_path)
    mapping_file = tmp_path / "mapping.json"
    assert mapping_file.exists()
    data = json.loads(mapping_file.read_text())
    assert "api_reference" in data


# ---------------------------------------------------------------------------
# Ignore list
# ---------------------------------------------------------------------------

def test_scan_excludes_node_modules(tmp_path):
    make_project(tmp_path, {
        "node_modules/express/index.js": "module.exports = {}",
        "app.js": "const express = require('express')",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert not any("node_modules" in f for f in all_files)


def test_scan_excludes_pycache(tmp_path):
    make_project(tmp_path, {
        "__pycache__/main.cpython-311.pyc": b"\x00\x00\x00\x00",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert not any("__pycache__" in f for f in all_files)


def test_scan_excludes_dotgit(tmp_path):
    make_project(tmp_path, {
        ".git/HEAD": "ref: refs/heads/main",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert not any(".git" in f for f in all_files)


def test_scan_excludes_venv(tmp_path):
    make_project(tmp_path, {
        "venv/lib/python3.11/site-packages/fastapi/__init__.py": "# fastapi",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert not any("venv" in f for f in all_files)


def test_scan_excludes_pyc_files(tmp_path):
    make_project(tmp_path, {
        "main.pyc": b"\x00compiled",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert not any(f.endswith(".pyc") for f in all_files)


def test_scan_excludes_lock_files(tmp_path):
    make_project(tmp_path, {
        "package-lock.json": '{"lockfileVersion": 2}',
        "yarn.lock": "# yarn lock",
        "Pipfile.lock": '{"default": {}}',
        "app.js": "console.log('hi')",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert "package-lock.json" not in all_files
    assert "yarn.lock" not in all_files
    assert "Pipfile.lock" not in all_files


# ---------------------------------------------------------------------------
# Binary file exclusion
# ---------------------------------------------------------------------------

def test_scan_excludes_binary_files(tmp_path):
    make_project(tmp_path, {
        "logo.png": b"\x89PNG\r\n\x1a\n\x00\x00",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert "logo.png" not in all_files


def test_scan_excludes_non_utf8_text(tmp_path):
    make_project(tmp_path, {
        "broken.txt": b"\xff\xfe invalid utf-8 \x80",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    all_files = _all_files(result)
    assert "broken.txt" not in all_files


# ---------------------------------------------------------------------------
# Section mapping — API Reference
# ---------------------------------------------------------------------------

def test_fastapi_routes_map_to_api_reference(tmp_path):
    make_project(tmp_path, {
        "routes/auth.py": "from fastapi import APIRouter\nrouter = APIRouter()",
        "routes/users.py": "from fastapi import APIRouter\nrouter = APIRouter()",
        "main.py": "from fastapi import FastAPI\napp = FastAPI()",
    })
    result = scan(tmp_path)
    api_files = result["api_reference"]
    assert any("routes/auth.py" in f for f in api_files)
    assert any("routes/users.py" in f for f in api_files)


def test_api_directory_maps_to_api_reference(tmp_path):
    make_project(tmp_path, {
        "api/v1/users.py": "# users endpoint",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("api/v1/users.py" in f for f in result["api_reference"])


def test_router_filename_maps_to_api_reference(tmp_path):
    make_project(tmp_path, {
        "user_router.py": "# router",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("user_router.py" in f for f in result["api_reference"])


# ---------------------------------------------------------------------------
# Section mapping — Getting Started
# ---------------------------------------------------------------------------

def test_requirements_txt_maps_to_getting_started(tmp_path):
    make_project(tmp_path, {
        "requirements.txt": "fastapi\nuvicorn",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("requirements.txt" in f for f in result["getting_started"])


def test_package_json_maps_to_getting_started(tmp_path):
    make_project(tmp_path, {
        "package.json": '{"name": "app"}',
        "index.js": "// entry",
    })
    result = scan(tmp_path)
    assert any("package.json" in f for f in result["getting_started"])


def test_top_level_readme_maps_to_getting_started(tmp_path):
    make_project(tmp_path, {
        "README.md": "# My Project",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("README.md" in f for f in result["getting_started"])


# ---------------------------------------------------------------------------
# Section mapping — Deployment
# ---------------------------------------------------------------------------

def test_dockerfile_maps_to_deployment(tmp_path):
    make_project(tmp_path, {
        "Dockerfile": "FROM python:3.11\nCOPY . .",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("Dockerfile" in f for f in result["deployment"])


def test_docker_compose_maps_to_deployment(tmp_path):
    make_project(tmp_path, {
        "docker-compose.yml": "version: '3'",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("docker-compose.yml" in f for f in result["deployment"])


def test_github_workflow_maps_to_deployment(tmp_path):
    make_project(tmp_path, {
        ".github/workflows/deploy.yml": "on: push",
        "main.py": "x = 1",
    })
    result = scan(tmp_path)
    assert any("deploy.yml" in f for f in result["deployment"])


# ---------------------------------------------------------------------------
# Section mapping — Architecture (tree string, not file list)
# ---------------------------------------------------------------------------

def test_architecture_is_string(tmp_path):
    make_project(tmp_path, {"src/main.py": "x = 1"})
    result = scan(tmp_path)
    assert isinstance(result["architecture"], str)
    assert len(result["architecture"]) > 0


def test_architecture_contains_directory_names(tmp_path):
    make_project(tmp_path, {"src/main.py": "x = 1", "tests/test_main.py": "x = 1"})
    result = scan(tmp_path)
    assert "src" in result["architecture"]


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _all_files(mapping: dict) -> list[str]:
    """Collect all file entries (non-architecture) from the mapping."""
    files = []
    for key, value in mapping.items():
        if key == "architecture":
            continue
        if isinstance(value, list):
            files.extend(value)
    return files
