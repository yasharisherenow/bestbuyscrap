"""Configuration helpers for the monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CATEGORY_URL = (
    "https://www.bestbuy.ca/en-ca/category/gaming-desktop-computers/30441"
    "?path=category%253AComputers%2B%2526%2BTablets%253Bcategory%253ADesktop%2B"
    "Computers%253Bcategory%253AGaming%2BDesktop%2BComputers%253B"
    "currentoffers0enrchstring%253AOn%2BClearance"
)


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from environment variables."""

    category_url: str = DEFAULT_CATEGORY_URL
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    request_timeout_sec: int = 20
    max_retries: int = 4
    backoff_factor: float = 1.5
    user_agent: str = "bestbuy-clearance-monitor/1.0"
    state_path: Path = Path("data/state.json")
    last_run_path: Path = Path("data/last_run.json")
    watchlist_path: Path = Path("data/watchlist.json")

    @property
    def telegram_enabled(self) -> bool:
        """Return whether Telegram credentials are configured."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def _clamp_int(value: str, default: int, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, minimum)


def _clamp_float(value: str, default: float, minimum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, minimum)


def load_config() -> Config:
    """Load configuration from environment with safe defaults."""
    timeout = _clamp_int(os.getenv("REQUEST_TIMEOUT_SEC", "20"), default=20, minimum=1)
    max_retries = _clamp_int(os.getenv("MAX_RETRIES", "4"), default=4, minimum=1)
    backoff = _clamp_float(os.getenv("BACKOFF_FACTOR", "1.5"), default=1.5, minimum=1.0)

    return Config(
        category_url=os.getenv("CATEGORY_URL", DEFAULT_CATEGORY_URL),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        request_timeout_sec=timeout,
        max_retries=max_retries,
        backoff_factor=backoff,
        user_agent=os.getenv("USER_AGENT", "bestbuy-clearance-monitor/1.0"),
        state_path=Path(os.getenv("STATE_PATH", "data/state.json")),
        last_run_path=Path(os.getenv("LAST_RUN_PATH", "data/last_run.json")),
        watchlist_path=Path(os.getenv("WATCHLIST_PATH", "data/watchlist.json")),
    )
