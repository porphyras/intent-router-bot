# ShopMate — intent-routing Telegram assistant for a retail store

![tests](https://github.com/puoku/intent-router-bot/actions/workflows/test.yml/badge.svg)

A Telegram bot plus a web admin panel for a small shop. It answers FAQs, searches the catalog,
and takes orders and reservations. Free-form messages go to an LLM that classifies the intent
and extracts order items. When the LLM is slow or unavailable, the bot falls back to rule-based handling.

Originally built for a real store; the catalog, address and contacts in this repository are demo data.

## Features

- **FAQ answers.** Address, opening hours, delivery, payment, returns, pickup, contacts. Fuzzy matching via `rapidfuzz`.
- **Catalog search.**
  - One match: a product card with price and stock.
  - Several matches: a short list to choose from.
- **Orders and reservations.**
  - Step-by-step dialog (FSM).
  - Or a single free-text message, e.g. "can I reserve 2 toothpastes until Wednesday?", parsed by the LLM.
- **Two-step confirmation.** The customer confirms the request in Telegram. A manager then confirms stock in the admin panel. Stock changes only after the manager's confirmation.
- **Admin panel** (FastAPI + Jinja2, HTTP Basic Auth).
  - Orders and reservations with statuses.
  - Product and FAQ editing.
  - CSV catalog import: preview, insert-only or upsert, with an import log.

## How a message is processed

```
message
  │
  ├─ 1. cheap checks, no LLM: trigger words, exact product match, fuzzy FAQ match
  │
  ├─ 2. otherwise → LLM classifier → JSON { intent, items[], reserve_until, faq_intent, product_query }
  │
  └─ 3. route by intent: FAQ answer · product search · order dialog · reservation
```

The LLM call is wrapped in a timeout, SDK retries are disabled, and a circuit breaker opens after N consecutive
failures. If the provider is down, the bot keeps working on rules only.
The LLM client works with any OpenAI-compatible endpoint (OpenAI, OpenRouter, ProxyAPI, …).

## Stack

| Area | Tools |
|---|---|
| Runtime | Python 3.12, asyncio |
| Bot | aiogram 3 (long polling) |
| Admin panel | FastAPI + Jinja2, served in the same process as the bot |
| Database | SQLAlchemy 2.0 — SQLite by default, PostgreSQL with `pg_trgm` indexes |
| Matching | rapidfuzz — fuzzy product and FAQ matching |
| LLM | OpenAI SDK — intent classification and item extraction |
| Ops | pytest, GitHub Actions, Docker Compose |

## Run locally

```sh
cp .env.example .env          # set BOT_TOKEN, OPENAI_API_KEY, ADMIN_PASSWORD
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

- Admin panel: http://localhost:8000/admin/
- Health check: http://localhost:8000/health

Or with Docker:

```sh
cp .env.example .env
docker compose up -d
```

## Configuration

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | Any OpenAI-compatible provider |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Admin panel login |
| `DATABASE_URL` | SQLite by default; set a PostgreSQL URL to switch |
| `LLM_TIMEOUT_SECONDS`, `LLM_RETRIES` | Per-request timeout and retries |
| `LLM_CIRCUIT_FAIL_THRESHOLD`, `LLM_CIRCUIT_OPEN_SECONDS` | Circuit breaker |
| `PARTNER_PRICE_MULTIPLIER` | Retail price = partner price × multiplier |

## CSV import

Semicolon-separated UTF-8 files. Column headers can be in English or Russian:
`name`, `price_partner`, `quantity`, `pv`, `category`, `aliases`, `description`, `sku`.
Numbers like `1 200,50` are parsed correctly.

## Tests

```sh
pytest
```

The tests cover CSV parsing and import, product search, order logic, and LLM fallback behaviour.

## Project layout

```
app/
├── bot/         # aiogram handlers, FSM states, keyboards
├── db/          # SQLAlchemy models, session, demo seed data
├── services/    # orders, product search, LLM client, FAQ, CSV import
├── templates/   # admin panel templates
├── config.py    # settings (pydantic-settings)
├── main.py      # FastAPI app + bot startup
└── web_admin.py # admin routes
```

## Known limitations

- **Manager buttons inside Telegram.** The code exists but is disabled: it needs a separate manager chat.
- **Database migrations.** None; the schema is created with `create_all`.
- **HTTPS.** The admin panel should sit behind a reverse proxy with HTTPS in production.
