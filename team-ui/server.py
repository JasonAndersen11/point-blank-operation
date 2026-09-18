#!/usr/bin/env python3
"""Point Blank Operation — local kickoff UI server.

Serves the team start-search page and forwards requests to the Grok Bot
webhook. The sender key is read from local config / env only — never sent
to the browser.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
CONFIG_PATH = ROOT / "config.json"
WEBHOOK_TIMEOUT_S = 8.0

# Two-letter code, or a place name (e.g. TX, Texas, New York).
STATE_RE = re.compile(r"^[A-Za-z]{2}$|^[A-Za-z][A-Za-z .'-]{1,58}$")

app = FastAPI(title="Point Blank Operation", docs_url=None, redoc_url=None)


class StartRequest(BaseModel):
    niche: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    city: Optional[str] = None

    @field_validator("niche", "state")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("This field is required")
        return value

    @field_validator("state")
    @classmethod
    def valid_state(cls, value: str) -> str:
        if not STATE_RE.match(value):
            raise ValueError("Use a 2-letter code or full name")
        if len(value) == 2:
            return value.upper()
        return value

    @field_validator("city")
    @classmethod
    def empty_city(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


def _load_config() -> dict[str, str]:
    """Env vars override config.json. Missing keys stay empty strings."""
    data: dict[str, str] = {}
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = {str(k): "" if v is None else str(v) for k, v in loaded.items()}
        except (OSError, json.JSONDecodeError):
            data = {}
    url = os.environ.get("WEBHOOK_URL", data.get("WEBHOOK_URL", "")).strip()
    key = os.environ.get("WEBHOOK_KEY", data.get("WEBHOOK_KEY", "")).strip()
    return {"WEBHOOK_URL": url, "WEBHOOK_KEY": key}


def _webhook_credentials() -> Optional[tuple[str, str]]:
    cfg = _load_config()
    url, key = cfg["WEBHOOK_URL"], cfg["WEBHOOK_KEY"]
    if not url or not key:
        return None
    return url, key


def _unconfigured() -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "error": (
                "Webhook is not configured. Copy config.example.json to "
                "config.json and fill WEBHOOK_URL and WEBHOOK_KEY "
                "(or set those environment variables)."
            ),
        },
        status_code=503,
    )


async def _post_webhook(payload: dict[str, Any]) -> JSONResponse:
    creds = _webhook_credentials()
    if creds is None:
        return _unconfigured()
    url, key = creds
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "X-Automation-Key": key,
    }
    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_S) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException:
        return JSONResponse(
            {"ok": False, "error": "Webhook timed out after 8 seconds."},
            status_code=504,
        )
    except httpx.RequestError:
        return JSONResponse(
            {"ok": False, "error": "Could not reach the Grok Bot webhook."},
            status_code=502,
        )

    if response.is_success:
        return JSONResponse(
            {
                "ok": True,
                "status": response.status_code,
                "action": payload.get("action"),
            }
        )

    detail = (response.text or "").strip()
    if len(detail) > 280:
        detail = detail[:277] + "..."
    return JSONResponse(
        {
            "ok": False,
            "error": f"Webhook returned HTTP {response.status_code}.",
            "detail": detail or None,
        },
        status_code=502,
    )


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/api/health")
async def health() -> dict[str, Any]:
    creds = _webhook_credentials()
    return {
        "status": "ok",
        "webhook_configured": creds is not None,
    }


@app.post("/api/ping")
async def ping() -> JSONResponse:
    return await _post_webhook({"action": "ping"})


@app.post("/api/start")
async def start_search(request: StartRequest) -> JSONResponse:
    payload: dict[str, Any] = {
        "action": "start_search",
        "niche": request.niche,
        "state": request.state,
    }
    if request.city:
        payload["city"] = request.city
    return await _post_webhook(payload)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run(app, host="0.0.0.0", port=port)
