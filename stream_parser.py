"""Stream source resolution for KinoKino.

Resolves playable HLS streams for a Kinopoisk ID by querying the public
players aggregator and extracting ``master.m3u8`` URLs from the provider
iframe players (currently the Alloha/theatre provider is supported).

The CDN only requires ``Origin``/``Referer`` headers matching the provider
domain, so a local proxy can forward manifest and segment requests with the
appropriate headers (see :mod:`main`).

Legal notice: this code only implements playback of streams the user is
already able to watch in their browser. It does not bypass DRM or paid
access controls. Do not use it to redistribute content you do not have
the rights to.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

PLAYERS_API_URL = "https://playcdnfb.top/api/players"
PLAYERS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; RMX3370) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://fixtyflux.cfd",
    "Referer": "https://fixtyflux.cfd/",
}

IFRAME_HEADERS = {
    "User-Agent": PLAYERS_HEADERS["User-Agent"],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://fixtyflux.cfd",
    "Referer": "https://fixtyflux.cfd/",
}

# Headers forwarded to the stream CDN (they only require Origin/Referer).
STREAM_HEADERS = {
    "User-Agent": PLAYERS_HEADERS["User-Agent"],
    "Origin": "https://theatre.stravers.live",
    "Referer": "https://theatre.stravers.live/",
}

_SESSION = requests.Session()

_M3U8_RE = re.compile(r"https?://[^\s\"'<>\\]+\.m3u8[^\s\"'<>\\]*")


def get_players(kinopoisk_id: int) -> list[dict[str, Any]]:
    """Return the raw provider list for a Kinopoisk ID."""

    response = _SESSION.get(
        PLAYERS_API_URL,
        params={"kinopoisk": kinopoisk_id},
        headers=PLAYERS_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or []
    return data if isinstance(data, list) else []


def _extract_master_url(iframe_html: str) -> str | None:
    """Extract the first ``master.m3u8`` URL from provider iframe HTML."""

    match = _M3U8_RE.search(iframe_html)
    return match.group(0) if match else None


def resolve_stream(iframe_url: str) -> dict[str, Any] | None:
    """Resolve a provider iframe into an HLS manifest URL.

    Returns ``{"manifest_url": ..., "provider_base": ...}`` or ``None``.
    """

    try:
        response = _SESSION.get(iframe_url, headers=IFRAME_HEADERS, timeout=20)
        response.raise_for_status()
    except Exception:
        return None

    master = _extract_master_url(response.text)
    if not master:
        return None
    return {
        "manifest_url": master,
        "provider_base": "https://theatre.stravers.live",
    }


def get_translations(kinopoisk_id: int) -> list[dict[str, Any]]:
    """List available translations/qualities for a Kinopoisk ID.

    Only providers whose iframe can be resolved to an HLS manifest are
    included; each entry carries a ``translation`` id that is later passed to
    the manifest endpoint.
    """

    providers = get_players(kinopoisk_id)
    results: list[dict[str, Any]] = []

    for provider in providers:
        ptype = provider.get("type") or "unknown"
        translations = provider.get("translations") or []
        base_iframe = provider.get("iframeUrl")

        candidates: list[dict[str, Any]] = []
        if translations:
            for tr in translations:
                if not isinstance(tr, dict):
                    continue
                candidates.append(
                    {
                        "translation_id": tr.get("id"),
                        "name": tr.get("name") or "Неизвестная озвучка",
                        "quality": tr.get("quality") or "",
                        "iframe_url": tr.get("iframeUrl") or base_iframe,
                    }
                )
        elif base_iframe:
            candidates.append(
                {
                    "translation_id": None,
                    "name": ptype,
                    "quality": "",
                    "iframe_url": base_iframe,
                }
            )

        for cand in candidates:
            if not cand.get("iframe_url"):
                continue
            resolved = resolve_stream(cand["iframe_url"])
            if not resolved:
                continue
            results.append(
                {
                    "provider": ptype,
                    "translation_id": cand["translation_id"],
                    "name": cand["name"],
                    "quality": cand["quality"],
                    "manifest_url": resolved["manifest_url"],
                }
            )
            # One resolvable entry per provider/translation is enough; the
            # manifest itself advertises all available qualities.
            break

    return results


def fetch_manifest(url: str) -> str:
    """Fetch a manifest (master or media playlist) with CDN headers."""

    response = _SESSION.get(url, headers=STREAM_HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def fetch_segment(url: str, range_header: str | None = None):
    """Fetch a binary segment with CDN headers, streaming the body."""

    headers = dict(STREAM_HEADERS)
    if range_header:
        headers["Range"] = range_header
    response = _SESSION.get(url, headers=headers, timeout=120, stream=True)
    response.raise_for_status()
    return response


def rewrite_playlist(text: str, base_url: str, manifest_proxy: str, segment_proxy: str) -> str:
    """Rewrite relative/absolute URIs in an M3U8 playlist to proxy URLs.

    Playlists (``.m3u8``) are routed through ``manifest_proxy``, binary
    fragments (segments, init files) through ``segment_proxy``. Both paths
    must contain a ``{url}`` placeholder that receives the URL-encoded
    absolute URL of the target.
    """

    from urllib.parse import quote

    def _proxy_for(target: str) -> str:
        path = urlparse(target).path.lower()
        if path.endswith(".m3u8"):
            return manifest_proxy
        return segment_proxy

    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue
        if stripped.startswith("#"):
            # Rewrite URIs inside tags like #EXT-X-MAP:URI="..." and #EXT-X-KEY:URI="..."
            def _tag_uri(match: re.Match[str]) -> str:
                raw = match.group(2)
                absolute = urljoin(base_url, raw)
                quoted = quote(absolute, safe="")
                return f'{match.group(1)}{_proxy_for(absolute).format(url=quoted)}{match.group(3)}'

            line = re.sub(
                r'(URI=")([^"]+)(")',
                _tag_uri,
                line,
            )
            lines.append(line)
            continue
        absolute = urljoin(base_url, stripped)
        quoted = quote(absolute, safe="")
        lines.append(_proxy_for(absolute).format(url=quoted))
    return "\n".join(lines) + "\n"
