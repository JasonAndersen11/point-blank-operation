# Point Blank Operation

Point Blank Operation is an AI-powered research pipeline based on the Flat Fee Mastery / Digital Landlords rank-and-rent research system. Built with CrewAI, FastAPI, and a real-time streaming UI.

## What It Does

Runs a 6-phase research pipeline to find and validate rank-and-rent opportunities:

- **Phase 1 — Keyword Research**: Builds a master keyword list for your niche using Semrush (cached for known niches — no API credits used)
- **Phase 2 — City Selection**: Finds qualifying cities in your target state (volume ≥30, CPC $0.01–$4.99). Stops after 3 passing cities to conserve credits
- **Phase 3 — Competitor Identification**: Identifies the top 3 Google Maps 3-pack competitors across 10+ keyword searches
- **Phase 4 — Due Diligence**: Scores each competitor on 4 metrics (domain age, backlinks, content depth, organic page 1 presence) and delivers a GO/NO-GO verdict
- **Phase 5 — Prospect List**: Finds 7–12 businesses already paying for advertising — exportable as a styled Excel call sheet
- **Phase 6 — Ad Copy**: Writes complete Google Smart Campaign + Facebook Lead Ad copy ready to paste into the ad platforms

## Tech Stack

- **Backend**: FastAPI + Server-Sent Events (real-time streaming)
- **AI Pipeline**: CrewAI (multi-agent, sequential process)
- **LLM**: Claude Sonnet (Anthropic)
- **Data**: Semrush API, Serper API (Google Maps + Ads search)
- **Tools**: WHOIS domain age, BeautifulSoup content analyzer, persistent city result cache
- **Export**: openpyxl Excel generation

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/JasonAndersen11/point-blank-operation.git
cd point-blank-operation
```

## Team kickoff UI

To start a search from a browser without running this pipeline locally, use the Point Blank Operation page in [`team-ui/`](team-ui/README.md):

```bash
cd team-ui
python3 -m pip install -r requirements.txt
python3 server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Copy `config.example.json` to `config.json` and fill the Grok Bot webhook URL and key first. Results go to the Point Blank Operation Grok Bot group chat.
