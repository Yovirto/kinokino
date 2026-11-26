"""KinoKino Android application entry point.

This module starts a local Flask webserver on port 5000. The python-for-android
webview bootstrap loads ``http://127.0.0.1:5000/`` in a native Android WebView.

The app provides its own search and catalog interface built on top of the
public Kinopoisk suggest API. When the user taps "Смотреть" inside a card, the
application opens the corresponding ``kinokino.win`` URL inside the same
WebView.
"""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from kinopoisk_parser import search

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

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


def main() -> None:
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        threaded=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
