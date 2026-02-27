# Architecture Overview

## Overview
`Local LLM Chat` now consists of a FastAPI backend that serves a lightweight HTML/JS frontend, plus an optional `extract-text` service that handles rich file parsing. The application keeps chat state client-side (`localStorage`) and forwards chat messages to any OpenAI-compatible API endpoint.

```
┌──────────────┐      HTTP      ┌───────────────┐
│  Browser UI  │ ◀────────────▶ │ FastAPI App   │
│ (web/index.html, app.js) │      `/api/*` │ (src/server.py) │
└──────────────┘                └───────────────┘
                                       │
                                       │ HTTP
                                       ▼
                              OpenAI-compatible API
                                       │
                            (llm_client.py / requests)

┌──────────────┐
│ extract-text │
│  service     │
│(dockerized)  │
└──────────────┘
```

## Backend (FastAPI)

- `src/server.py`
  - Serves `/` (static HTML) and static assets (`/static/*`).
  - `/api/config`: returns defaults (model, API URL, extract-text URL, system prompt).
  - `/api/chat`: forwards chat history to the configured LLM using `src/utils/llm_client.py`, handles errors (including missing API key) and returns a single assistant message.
  - `/api/extract`: uploads files to the running extract-text service via `src/utils/extract_text_client.py` and returns the combined plain text.

## Frontend (Web)

Files under `web/`:

- `index.html`: shell layout with sidebar, message column, and settings drawer.
- `styles.css`: dark theme + layout; adds scrollbar, status area, and copy buttons.
- `app.js`: stores chat history/settings in `localStorage`, handles chat flow, file uploads, copy-to-clipboard, and status messages.

## Clients

- `src/utils/llm_client.py`: sends chat completions (messages + params) to the LLM endpoint; normalizes `Authorization` headers (trims spaces, allows sending pre-pended `Bearer`).
- `src/utils/extract_text_client.py`: POSTs files to the extract-text service and validates the response; raises descriptive errors when the service is unreachable.

## Configuration

- `.env.example` / environment variables: `API_URL`, `API_KEY`, `MODEL_NAME`, `EXTRACT_TEXT_API_URL`, `EXTRACT_TEXT_TIMEOUT`, `MAX_IMPORTED_CHARS`.
- Settings default to these values but can be overridden in the UI drawer.

## Docker

- `Dockerfile`: packages FastAPI + static web UI.
- `docker/extract-text.Dockerfile`: full extract-text service with LibreOffice, Tesseract, Playwright (Chromium), required fonts/libraries.
- `docker-compose.yml`: orchestrates both services; sets the chat app to point at `http://extract-text:7555`.
- `.dockerignore`: prevents unnecessary files from copying into the image.

## Running

1. `python run.py` (requires extract-text reachable at `EXTRACT_TEXT_API_URL`, otherwise only chat works).
2. `docker compose up --build` to start chat + extract-text together (preferred for file import/export).

If the extract-text service is unreachable, the UI displays an “extract-text is unreachable” status and file extraction gracefully skips. The chat flow continues independently.
