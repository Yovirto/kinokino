"""HTTP client for Kinopoisk suggest API.

The public suggest endpoint does not require an API key:

    https://www.kinopoisk.ru/api/suggest/v2/?query=Inception

It returns JSON with films, series and persons. This module extracts only the
fields needed for our own catalog interface: id, Russian/original title,
rating, year and poster URL.
"""

from __future__ import annotations

import json
import re
from typing import Any

import requests

KINOPOISK_SUGGEST_URL = "https://www.kinopoisk.ru/api/suggest/v2/"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; RMX3370) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.kinopoisk.ru/",
    "Origin": "https://www.kinopoisk.ru",
    "X-Requested-With": "XMLHttpRequest",
}

_SESSION = requests.Session()


def _poster_url(item: dict[str, Any]) -> str | None:
    """Return an absolute poster URL or ``None``."""

    gallery = item.get("gallery") or {}
    posters = gallery.get("posters") or {}
    vertical = posters.get("kpVertical") or {}
    url = vertical.get("avatarsUrl")
    if url:
        return "https:" + url if url.startswith("//") else url
    hd = posters.get("hdVertical") or {}
    url = hd.get("avatarsUrl")
    if url:
        return "https:" + url if url.startswith("//") else url
    return None


def _title(item: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (russian_title, original_title)."""

    title = item.get("title") or {}
    return title.get("russian"), title.get("original")


def _rating(item: dict[str, Any]) -> float | None:
    rating = item.get("rating") or {}
    kp = rating.get("kinopoisk") or {}
    value = kp.get("value")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _year(item: dict[str, Any]) -> int | None:
    year = item.get("productionYear")
    try:
        return int(year) if year is not None else None
    except (TypeError, ValueError):
        return None


def _item_id(item: dict[str, Any]) -> int | None:
    value = item.get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _clean_item(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one suggest API item into our catalog shape."""

    item_id = _item_id(raw)
    if item_id is None:
        return None

    russian, original = _title(raw)
    return {
        "id": item_id,
        "title": russian or original or "",
        "original_title": original or "",
        "rating": _rating(raw),
        "year": _year(raw),
        "poster": _poster_url(raw),
        "url": f"https://www.kinopoisk.ru/film/{item_id}/",
    }


def search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search films and series on Kinopoisk by keyword."""

    if not query or not query.strip():
        return []

    try:
        response = _SESSION.get(
            KINOPOISK_SUGGEST_URL,
            params={"query": query.strip()},
            headers=REQUEST_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    suggest = data.get("suggest") or {}

    top = suggest.get("top") or {}
    top_result = top.get("topResult") or {}
    global_result = top_result.get("global") or {}
    if global_result:
        item = _clean_item(global_result)
        if item:
            results.append(item)

    movies = top.get("movies") or []
    for raw in movies[:limit]:
        item = _clean_item(raw)
        if item and item not in results:
            results.append(item)

    series = top.get("series") or []
    for raw in series[:limit]:
        item = _clean_item(raw)
        if item and item not in results:
            results.append(item)

    people = top.get("people") or []
    for raw in people[:limit]:
        item = _clean_item(raw)
        if item and item not in results:
            results.append(item)

    # Fallback: some responses place results directly inside ``suggest``.
    for key in ("films", "results", "items"):
        block = suggest.get(key)
        if isinstance(block, list):
            for raw in block[:limit]:
                item = _clean_item(raw)
                if item and item not in results:
                    results.append(item)

    return results[:limit]
