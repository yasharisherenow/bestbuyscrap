"""Telegram notification helpers."""

from __future__ import annotations

import html
import logging
from typing import Iterable

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Simple Telegram Bot API client."""

    def __init__(self, bot_token: str, chat_id: str, timeout_sec: int = 20) -> None:
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self.timeout_sec = timeout_sec

    def send_text(self, text: str) -> None:
        """Send one message using safe HTML formatting and no previews."""
        response = requests.post(
            f"{self.base_url}/sendMessage",
            timeout=self.timeout_sec,
            json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        response.raise_for_status()

    def send_many(self, chunks: Iterable[str]) -> int:
        """Send multiple message chunks and return count."""
        count = 0
        for chunk in chunks:
            self.send_text(chunk)
            count += 1
        return count


def build_summary_messages(diff: dict[str, list[dict[str, object]]], max_len: int = 3500) -> list[str]:
    """Build compact text summary and split into Telegram-safe chunks."""
    lines: list[str] = ["<b>Best Buy Clearance Monitor</b>"]

    if diff["added"]:
        lines.append(f"\n<b>Added ({len(diff['added'])})</b>")
        for item in diff["added"]:
            current = item["current"]
            lines.append(
                "• {name} | ${price} | online={online} | pickup={pickup}\n"
                "  SKU: {sku}\n"
                "  {url}".format(
                    name=html.escape(str(current.get("name", "Unknown"))),
                    price=html.escape(str(current.get("price", "?"))),
                    online=html.escape(str(current.get("online_availability", "unknown"))),
                    pickup=html.escape(str(current.get("pickup_availability", "unknown"))),
                    sku=html.escape(str(current.get("sku", ""))),
                    url=html.escape(str(current.get("url", ""))),
                )
            )

    if diff["changed"]:
        lines.append(f"\n<b>Changed ({len(diff['changed'])})</b>")
        for item in diff["changed"]:
            current = item["current"]
            changes = item["changes"]
            lines.append(
                "• {name} (SKU: {sku})\n"
                "  {url}\n"
                "  online raw: {delivery_raw}\n"
                "  pickup raw: {pickup_raw}".format(
                    name=html.escape(str(current.get("name", "Unknown"))),
                    sku=html.escape(str(current.get("sku", ""))),
                    url=html.escape(str(current.get("url", ""))),
                    delivery_raw=html.escape(str(current.get("delivery_raw", ""))),
                    pickup_raw=html.escape(str(current.get("pickup_raw", ""))),
                )
            )
            for field, (old_val, new_val) in changes.items():
                lines.append(
                    "    - {field}: {old} → {new}".format(
                        field=html.escape(field),
                        old=html.escape(str(old_val)),
                        new=html.escape(str(new_val)),
                    )
                )

    if diff["removed"]:
        lines.append(f"\n<b>Removed ({len(diff['removed'])})</b>")
        for item in diff["removed"]:
            previous = item["previous"]
            lines.append(
                "• {name} (SKU: {sku})\n  {url}".format(
                    name=html.escape(str(previous.get("name", "Unknown"))),
                    sku=html.escape(str(previous.get("sku", ""))),
                    url=html.escape(str(previous.get("url", ""))),
                )
            )

    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)

    return chunks
