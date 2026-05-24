"""Tests for the upload page (Issue 1 — project scaffold)."""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_upload_page_has_zip_file_input():
    response = client.get("/")
    assert 'accept=".zip"' in response.text


def test_upload_page_has_quick_mode():
    response = client.get("/")
    assert "Quick" in response.text
    # The value must be submitted with the form
    assert 'value="quick"' in response.text


def test_upload_page_has_comprehensive_mode():
    response = client.get("/")
    assert "Comprehensive" in response.text
    assert 'value="comprehensive"' in response.text


def test_upload_page_form_posts_to_upload():
    response = client.get("/")
    html = response.text
    assert 'action="/upload"' in html or "action='/upload'" in html
    assert 'method="post"' in html.lower() or "method='post'" in html.lower()


def test_upload_page_includes_tailwind_cdn():
    response = client.get("/")
    assert "tailwindcss" in response.text or "cdn.tailwindcss" in response.text
