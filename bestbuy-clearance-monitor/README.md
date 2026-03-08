# Best Buy Clearance Monitor

Production-ready Python monitor for **Best Buy Canada Gaming Desktop Clearance** that:

1. Scrapes category product links.
2. Visits each product page.
3. Parses product details and availability.
4. Stores current state in `data/state.json`.
5. Diffs against previous state.
6. Sends Telegram alerts only on meaningful changes.
7. Stores run metadata in `data/last_run.json`.
8. Runs automatically in GitHub Actions and commits updated state files back to the repo.

## Target Category

- `https://www.bestbuy.ca/en-ca/category/gaming-desktop-computers/30441?path=category%253AComputers%2B%2526%2BTablets%253Bcategory%253ADesktop%2BComputers%253Bcategory%253AGaming%2BDesktop%2BComputers%253Bcurrentoffers0enrchstring%253AOn%2BClearance`

## Project Structure

```text
bestbuy-clearance-monitor/
  .github/workflows/monitor.yml
  src/__init__.py
  src/config.py
  src/scraper.py
  src/parser.py
  src/state_manager.py
  src/diffing.py
  src/notifier.py
  src/main.py
  data/state.json
  data/last_run.json
  data/watchlist.json
  tests/test_diffing.py
  tests/test_parser.py
  tests/test_state_manager.py
  README.md
  requirements.txt
  sample.env
  .gitignore
```

## Setup

### 1) Create virtualenv and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment variables

Copy `sample.env` values to your shell or CI environment:

- `TELEGRAM_BOT_TOKEN` (required for Telegram notifications)
- `TELEGRAM_CHAT_ID` (required for Telegram notifications)

Optional:

- `CATEGORY_URL`
- `REQUEST_TIMEOUT_SEC`
- `MAX_RETRIES`
- `BACKOFF_FACTOR`

## Telegram Setup

### Create bot token

1. Open Telegram and message `@BotFather`.
2. Run `/newbot` and follow prompts.
3. Copy the generated bot token.

### Get chat ID

Common options:

1. Start chat with your bot (or add bot to a group).
2. Send any message to the bot/group.
3. Open this URL in browser (replace token):
   - `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates`
4. Find `chat.id` in the JSON response.

For groups, the chat ID is often negative (for example `-100...`).

## Watchlist Filtering

`data/watchlist.json` supports optional filtering:

```json
{
  "skus": ["12345678"],
  "keywords": ["rtx 4070", "intel i7"]
}
```

Behavior:

- If both arrays are empty, all products are monitored.
- If populated, a product is tracked when:
  - SKU is in `skus`, or
  - any keyword matches name/spec text/url.

## Availability Normalization

Online availability maps to:

- `available_online`
- `sold_out_online`
- `not_available_for_delivery`
- `unknown`

Pickup availability maps to:

- `available_for_pickup`
- `not_available_for_pickup`
- `unknown`

Diff logic compares normalized statuses first and includes raw availability strings in alert text for context.

## Local Run

From project root (`bestbuy-clearance-monitor/`):

```bash
python -m src.main
```

Logs are printed to stdout (suitable for CI logs).

## GitHub Actions

Workflow file: `.github/workflows/monitor.yml`

Features:

- `workflow_dispatch` for manual runs.
- `schedule` cron every 30 minutes.
- Python setup and dependency install.
- Runs `python -m src.main`.
- Commits and pushes `data/state.json` and `data/last_run.json` when changed.

### Required GitHub Secrets

In repo settings, add:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## State Persistence

- `data/state.json`: full product snapshot keyed by SKU (fallback URL).
- `data/last_run.json`: run metadata (`last_run_utc`, `products_seen`, `alerts_sent`, `status`).
- `data/watchlist.json`: optional SKU/keyword filter.

These files are versioned so GitHub Actions can keep historical state between runs via git commits.
