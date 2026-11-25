"""Rules for converting a KinoPoisk page URL to its KinoKino counterpart."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

KINOPOISK_START_URL = "https://www.kinopoisk.ru/"
KINOKINO_HOST = "www.kinokino.win"

ALLOWED_SOURCE_HOSTS = frozenset({"kinopoisk.ru", "www.kinopoisk.ru"})
ALLOWED_SOURCE_SCHEMES = frozenset({"http", "https"})

# A supported page consists of two path segments. The first one may contain
# any non-empty value (for example, ``film`` or ``series``), while the second
# one is the numeric KinoPoisk object ID.
_MOVIE_PATH_RE = re.compile(r"^/[^/]+/[0-9]+/?$")


def build_mirror_url(source_url: str | None) -> str | None:
    """Return the KinoKino URL for a supported KinoPoisk URL.

    The path and query string are preserved. ``None`` is returned when the
    source URL is malformed, belongs to another host, or does not point to a
    page in the ``/<type>/<numeric-id>/`` format.
    """

    if not source_url:
        return None

    try:
        parts = urlsplit(source_url)
        # Accessing ``port`` also validates malformed port values.
        parts.port
    except ValueError:
        return None

    if parts.scheme.lower() not in ALLOWED_SOURCE_SCHEMES:
        return None

    hostname = parts.hostname
    if hostname is None or hostname.lower() not in ALLOWED_SOURCE_HOSTS:
        return None

    # Reject credentials and non-standard ports to avoid accepting deceptive
    # URLs that only look like KinoPoisk links.
    if parts.username is not None or parts.password is not None:
        return None
    if parts.port is not None:
        return None

    if not _MOVIE_PATH_RE.fullmatch(parts.path):
        return None

    return urlunsplit(
        (
            "https",
            KINOKINO_HOST,
            parts.path,
            parts.query,
            parts.fragment,
        )
    )
