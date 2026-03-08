"""Entrypoint for Best Buy clearance monitor."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .config import load_config
from .diffing import compare_states, has_meaningful_changes
from .notifier import TelegramNotifier, build_summary_messages
from .parser import parse_product_page
from .scraper import Scraper
from .state_manager import load_json, load_watchlist, save_json


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def matches_watchlist(product: dict[str, str], watchlist: dict[str, list[str]]) -> bool:
    """Apply optional watchlist filtering by SKUs and keywords."""
    skus = set(watchlist.get("skus", []))
    keywords = watchlist.get("keywords", [])

    if not skus and not keywords:
        return True

    sku = product.get("sku", "")
    if sku and sku in skus:
        return True

    haystack = " ".join(
        [
            product.get("name", ""),
            product.get("brand", ""),
            product.get("cpu", ""),
            product.get("gpu", ""),
            product.get("url", ""),
        ]
    ).lower()

    return any(keyword in haystack for keyword in keywords)


def run() -> int:
    """Execute one monitor cycle."""
    setup_logging()
    config = load_config()
    logger = logging.getLogger("monitor")

    previous_state = load_json(config.state_path, {})
    watchlist = load_watchlist(config.watchlist_path)

    scraper = Scraper(
        timeout_sec=config.request_timeout_sec,
        max_retries=config.max_retries,
        backoff_factor=config.backoff_factor,
        user_agent=config.user_agent,
    )

    alerts_sent = 0
    status = "ok"
    current_state: dict[str, dict[str, str]] = {}

    try:
        product_links = scraper.collect_product_links(config.category_url)
        pages = scraper.fetch_product_pages(product_links)

        for url, html in pages.items():
            product = parse_product_page(url, html)
            if not matches_watchlist(product, watchlist):
                continue
            key = product.get("sku") or product.get("url")
            if not key:
                continue
            current_state[key] = product

        diff = compare_states(previous_state, current_state)

        if has_meaningful_changes(diff):
            if config.telegram_enabled:
                messages = build_summary_messages(diff)
                notifier = TelegramNotifier(
                    bot_token=config.telegram_bot_token,
                    chat_id=config.telegram_chat_id,
                    timeout_sec=config.request_timeout_sec,
                )
                alerts_sent = notifier.send_many(messages)
                logger.info("Sent %s Telegram messages", alerts_sent)
            else:
                logger.warning("Changes found but Telegram is disabled (missing credentials)")

        save_json(config.state_path, current_state)

    except Exception:
        logger.exception("Monitor run failed")
        status = "error"

    last_run = {
        "last_run_utc": datetime.now(timezone.utc).isoformat(),
        "products_seen": len(current_state),
        "alerts_sent": alerts_sent,
        "status": status,
    }
    save_json(config.last_run_path, last_run)

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(run())
