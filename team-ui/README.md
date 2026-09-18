# Point Blank Operation — Team Kickoff UI

A small local page Jason can open to start a Flat Fee Mastery market search.

Submitting the form asks **this server** to POST JSON to the Point Blank Operation Grok Bot webhook. The webhook sender key stays on the machine — it is never embedded in browser JavaScript.

This UI does **not** run the CrewAI / Semrush pipeline itself. It only kicks off a run; results appear in the Point Blank Operation Grok Bot group chat.

## Configure

1. Copy the example config:

   ```bash
   cd team-ui
   cp config.example.json config.json
   ```

2. Fill in `WEBHOOK_URL` and `WEBHOOK_KEY` from the Grok Bot webhook settings.

   `config.json` is gitignored. Do not commit a real key.

Alternatively, set environment variables (these override the file):

```bash
export WEBHOOK_URL="https://..."
export WEBHOOK_KEY="..."
```

`config.example.json` ships with empty placeholders on purpose. There is no default webhook URL.

## Run

```bash
cd team-ui
python3 -m pip install -r requirements.txt
python3 server.py
```

Optional: use a venv (`python3 -m venv .venv && source .venv/bin/activate`) before installing.

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

The server binds `0.0.0.0` so it is reachable on the LAN. Default port is **8765** (`PORT` env var overrides it).

If the webhook is not configured yet, the page still loads. `POST /api/start` and `POST /api/ping` return HTTP 503 until `WEBHOOK_URL` and `WEBHOOK_KEY` are set.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Kickoff page |
| `GET` | `/api/health` | Liveness; `{ "status": "ok", "webhook_configured": true/false }` |
| `POST` | `/api/start` | Body `{ "niche", "state", "city?" }` → webhook `{ "action": "start_search", ... }` (`city` omitted when empty) |
| `POST` | `/api/ping` | Webhook `{ "action": "ping" }` for wiring tests |

Webhook request headers:

- `Content-Type: application/json`
- `Authorization: Bearer <key>`
- `X-Automation-Key: <key>`

Timeout is 8 seconds with no retry.

## Form

- **Niche** (required)
- **State** (required — 2-letter code or full name)
- **City** (optional)
- Primary button: **Start search**
