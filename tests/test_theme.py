"""Tests for static file serving: theme.css and Unageo font."""
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
