import json
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_home_serves_title_and_no_secrets(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "Point Blank Operation" in html
    assert "Start search" in html
    assert "Keyword Research" in html
    assert "City Selection" in html
    assert "Competitor Research" in html
    assert "Due Diligence" in html
    assert "Prospect Builder" in html
    assert "Ad Copy" in html
    assert "Point Blank Operation Grok Bot group chat" in html
    assert "WEBHOOK_KEY" not in html
    assert "Bearer " not in html
    assert "X-Automation-Key" not in html


def test_health_unconfigured(client, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WEBHOOK_KEY", raising=False)
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["webhook_configured"] is False


def test_start_requires_fields(client):
    res = client.post("/api/start", json={"niche": "", "state": "TX"})
    assert res.status_code == 422


def test_start_rejects_bad_state(client):
    res = client.post("/api/start", json={"niche": "roofing", "state": "T"})
    assert res.status_code == 422


def test_start_unconfigured(client, tmp_path, monkeypatch):
    monkeypatch.setattr(server, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WEBHOOK_KEY", raising=False)
    res = client.post("/api/start", json={"niche": "roofing", "state": "TX"})
    assert res.status_code == 503
    assert "not configured" in res.json()["error"]


def _ok_response(status=200):
    return httpx.Response(status, json={"ok": True})


def test_start_posts_webhook_omits_empty_city(client, monkeypatch):
    monkeypatch.setattr(server, "_webhook_credentials", lambda: ("http://webhook.test/hook", "secret-key"))
    captured = {}

    async def fake_post(self, url, json=None, headers=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return _ok_response()

    with patch.object(httpx.AsyncClient, "post", new=fake_post):
        res = client.post("/api/start", json={"niche": " dumpster rental ", "state": "tx", "city": "  "})

    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert captured["url"] == "http://webhook.test/hook"
    assert captured["json"] == {
        "action": "start_search",
        "niche": "dumpster rental",
        "state": "TX",
    }
    assert "city" not in captured["json"]
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["headers"]["X-Automation-Key"] == "secret-key"


def test_start_includes_city(client, monkeypatch):
    monkeypatch.setattr(server, "_webhook_credentials", lambda: ("http://webhook.test/hook", "secret-key"))
    captured = {}

    async def fake_post(self, url, json=None, headers=None):
        captured["json"] = json
        return _ok_response()

    with patch.object(httpx.AsyncClient, "post", new=fake_post):
        res = client.post(
            "/api/start",
            json={"niche": "roofing", "state": "Texas", "city": "Austin"},
        )

    assert res.status_code == 200
    assert captured["json"] == {
        "action": "start_search",
        "niche": "roofing",
        "state": "Texas",
        "city": "Austin",
    }


def test_ping_posts_action(client, monkeypatch):
    monkeypatch.setattr(server, "_webhook_credentials", lambda: ("http://webhook.test/hook", "secret-key"))
    captured = {}

    async def fake_post(self, url, json=None, headers=None):
        captured["json"] = json
        captured["headers"] = headers
        return _ok_response()

    with patch.object(httpx.AsyncClient, "post", new=fake_post):
        res = client.post("/api/ping")

    assert res.status_code == 200
    assert captured["json"] == {"action": "ping"}
    assert captured["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["headers"]["X-Automation-Key"] == "secret-key"


def test_webhook_timeout(client, monkeypatch):
    monkeypatch.setattr(server, "_webhook_credentials", lambda: ("http://webhook.test/hook", "secret-key"))

    async def fake_post(self, url, json=None, headers=None):
        raise httpx.TimeoutException("timeout")

    with patch.object(httpx.AsyncClient, "post", new=fake_post):
        res = client.post("/api/ping")

    assert res.status_code == 504
    assert "timed out" in res.json()["error"]


def test_config_file_loads(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"WEBHOOK_URL": "http://example.invalid/hook", "WEBHOOK_KEY": "abc"}))
    monkeypatch.setattr(server, "CONFIG_PATH", cfg)
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WEBHOOK_KEY", raising=False)
    assert server._webhook_credentials() == ("http://example.invalid/hook", "abc")
