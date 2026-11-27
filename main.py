"""KinoKino Android application entry point.

This module starts a local Flask webserver on port 5000. The python-for-android
webview bootstrap loads ``http://127.0.0.1:5000/`` in a native Android WebView.

The app provides its own search and catalog interface built on top of the
public Kinopoisk suggest API. When the user taps "Смотреть" inside a card, the
application opens the built-in HLS player (``/watch/<id>``), which resolves
available translations/qualities via the stream parser and plays the stream
through a local proxy that adds the required CDN headers.
"""

from __future__ import annotations

from flask import Flask, Response, jsonify, render_template, request

from kinopoisk_parser import search
from stream_parser import (
    fetch_manifest,
    fetch_segment,
    get_translations,
    rewrite_playlist,
)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

# Proxy endpoints used inside rewritten playlists.
MANIFEST_PROXY = "/stream/manifest?url={url}"
SEGMENT_PROXY = "/stream/segment?url={url}"

app = Flask(__name__)


@app.get("/")
def index():
    """Serve the custom catalog/search interface."""

    return render_template("index.html")


@app.get("/api/search")
def api_search():
    """Proxy Kinopoisk suggest results for the client interface."""

    query = request.args.get("q", "", type=str)
    limit = request.args.get("limit", 20, type=int)
    results = search(query)
    return jsonify({"results": results[: max(0, limit)]})


@app.get("/api/film/<int:film_id>")
def api_film(film_id: int):
    """Placeholder for a future film detail endpoint."""

    return jsonify(
        {
            "id": film_id,
            "url": f"https://www.kinopoisk.ru/film/{film_id}/",
            "mirror_url": f"https://www.kinokino.win/film/{film_id}/",
        }
    )


@app.get("/health")
def health():
    """Small local endpoint useful for diagnostics."""

    return "ok"


@app.get("/watch/<int:film_id>")
def watch(film_id: int):
    """Player page with translation/quality selection."""

    return render_template("watch.html", film_id=film_id)


@app.get("/api/film/<int:film_id>/streams")
def api_streams(film_id: int):
    """List resolvable translations/qualities for a Kinopoisk ID."""

    streams = get_translations(film_id)
    return jsonify({"results": streams})


@app.get("/stream/manifest")
def stream_manifest():
    """Proxy an HLS manifest, rewriting URIs to local proxy endpoints."""

    url = request.args.get("url", "", type=str)
    if not url or not url.startswith("http"):
        return jsonify({"error": "url parameter required"}), 400

    try:
        text = fetch_manifest(url)
    except Exception:
        return jsonify({"error": "manifest fetch failed"}), 502

    return Response(
        rewrite_playlist(text, url, MANIFEST_PROXY, SEGMENT_PROXY),
        content_type="application/vnd.apple.mpegurl",
    )


@app.get("/stream/segment")
def stream_segment():
    """Proxy a media segment or init fragment, streaming the body."""

    url = request.args.get("url", "", type=str)
    if not url or not url.startswith("http"):
        return jsonify({"error": "url parameter required"}), 400

    range_header = request.headers.get("Range")
    try:
        upstream = fetch_segment(url, range_header)
    except Exception:
        return jsonify({"error": "segment fetch failed"}), 502

    headers = {}
    if upstream.headers.get("Content-Range"):
        headers["Content-Range"] = upstream.headers["Content-Range"]
    if upstream.headers.get("Content-Length"):
        headers["Content-Length"] = upstream.headers["Content-Length"]
    headers["Accept-Ranges"] = "bytes"

    content_type = upstream.headers.get(
        "Content-Type", "application/octet-stream"
    )

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    status = 206 if range_header and "Content-Range" in headers else 200
    return Response(generate(), status=status, content_type=content_type, headers=headers)


@app.get("/player")
def player_redirect():
    """Convenience route: /player?kp=<id> opens the watch page."""

    film_id = request.args.get("kp", type=int)
    if not film_id:
        return jsonify({"error": "kp parameter required"}), 400
    return render_template("watch.html", film_id=film_id)


def main() -> None:
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        threaded=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
