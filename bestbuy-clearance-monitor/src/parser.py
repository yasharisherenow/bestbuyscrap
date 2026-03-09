"""Parsing and normalization for Best Buy product pages."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from bs4 import BeautifulSoup


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_online_availability(raw_text: str) -> str:
    """Normalize delivery text to stable enum-like values."""
    text = raw_text.lower()
    if any(
        k in text
        for k in (
            "sold out online",
            "out of stock online",
            "unavailable online",
            "not available online",
        )
    ):
        return "sold_out_online"
    if any(
        k in text
        for k in (
            "not available for delivery",
            "delivery unavailable",
            "delivery not available",
        )
    ):
        return "not_available_for_delivery"
    if any(
        k in text
        for k in (
            "available to ship",
            "available online",
            "get it shipped",
            "in stock online",
            "shipping available",
        )
    ):
        return "available_online"
    return "unknown"


def normalize_pickup_availability(raw_text: str) -> str:
    """Normalize pickup text to stable enum-like values."""
    text = raw_text.lower()
    if any(
        k in text
        for k in (
            "not available for pickup",
            "pickup unavailable",
            "pick up unavailable",
            "not available at",
            "pickup not available",
        )
    ):
        return "not_available_for_pickup"
    if any(
        k in text
        for k in (
            "available for pickup",
            "ready for pickup",
            "pick up as soon as",
            "in-store pickup available",
        )
    ):
        return "available_for_pickup"
    return "unknown"


def _extract_json_ld(soup: BeautifulSoup) -> Dict[str, Any]:
    for script in soup.select('script[type="application/ld+json"]'):
        text = script.string or script.get_text("", strip=True)
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    return item
        if isinstance(data, dict):
            if data.get("@type") == "Product":
                return data
            graph = data.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
    return {}


def _find_text_by_keywords(soup: BeautifulSoup, keywords: tuple[str, ...]) -> str:
    all_text = _normalize_whitespace(soup.get_text(" ", strip=True))
    for keyword in keywords:
        pattern = re.compile(rf"({re.escape(keyword)}[^.\n]{{0,120}})", re.IGNORECASE)
        match = pattern.search(all_text)
        if match:
            return _normalize_whitespace(match.group(1))
    return ""


def _extract_price_from_offers(offers: Any) -> str:
    if isinstance(offers, dict):
        return str(offers.get("price", "")).strip()
    if isinstance(offers, list):
        for offer in offers:
            if isinstance(offer, dict) and offer.get("price") is not None:
                return str(offer.get("price", "")).strip()
    return ""


def parse_product_page(url: str, html: str) -> dict[str, str]:
    """Parse a product page into normalized data fields."""
    soup = BeautifulSoup(html, "html.parser")
    product_json = _extract_json_ld(soup)

    name = ""
    if isinstance(product_json.get("name"), str):
        name = product_json["name"]
    if not name and soup.title:
        name = soup.title.get_text(strip=True)

    price = _extract_price_from_offers(product_json.get("offers", {}))
    if not price:
        price_tag = soup.select_one('[itemprop="price"]')
        if price_tag:
            price = price_tag.get("content", "") or price_tag.get_text(strip=True)

    sku = ""
    candidate_sku = product_json.get("sku") or product_json.get("productID")
    if isinstance(candidate_sku, str):
        sku = candidate_sku.strip()
    if not sku:
        text = soup.get_text(" ", strip=True)
        match = re.search(r"(?:Web\s*Code|SKU)\s*[:#]?\s*(\d{5,})", text, re.IGNORECASE)
        if match:
            sku = match.group(1)

    brand = ""
    brand_json = product_json.get("brand", "")
    if isinstance(brand_json, dict):
        brand = str(brand_json.get("name", "")).strip()
    elif isinstance(brand_json, str):
        brand = brand_json.strip()

    cpu = _find_text_by_keywords(soup, ("processor", "cpu"))
    ram = _find_text_by_keywords(soup, ("ram", "memory"))
    storage = _find_text_by_keywords(soup, ("storage", "ssd", "hard drive"))
    gpu = _find_text_by_keywords(soup, ("graphics", "gpu", "video card"))

    delivery_raw = _find_text_by_keywords(
        soup,
        (
            "available to ship",
            "sold out online",
            "not available for delivery",
            "available online",
            "delivery unavailable",
            "delivery",
        ),
    )
    pickup_raw = _find_text_by_keywords(
        soup,
        (
            "available for pickup",
            "not available for pickup",
            "ready for pickup",
            "pickup unavailable",
            "pickup",
        ),
    )

    return {
        "name": _normalize_whitespace(name),
        "price": _normalize_whitespace(price),
        "sku": sku,
        "brand": _normalize_whitespace(brand),
        "cpu": cpu,
        "ram": ram,
        "storage": storage,
        "gpu": gpu,
        "delivery_raw": delivery_raw,
        "pickup_raw": pickup_raw,
        "online_availability": normalize_online_availability(delivery_raw),
        "pickup_availability": normalize_pickup_availability(pickup_raw),
        "url": url,
    }
