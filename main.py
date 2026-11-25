"""KinoKino Android application entry point.

The python-for-android ``webview`` bootstrap starts this module and loads its
local Flask server in a native Android WebView. The native floating button
opens the ``/mirror`` endpoint with the current WebView URL; the actual URL
validation and conversion are performed here in Python.
"""

from __future__ import annotations

import sys
import traceback

from flask import Flask, redirect, request

from url_rules import KINOPOISK_START_URL, build_mirror_url

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

app = Flask(__name__)

_INVALID_URL_PAGE = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Неподходящая ссылка</title>
  <style>
    html, body { height: 100%; margin: 0; }
    body {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      box-sizing: border-box;
      background: #f7f7f7;
      color: #222;
      font: 16px/1.45 sans-serif;
      text-align: center;
    }
    .message { max-width: 420px; }
  </style>
</head>
<body>
  <div class="message">
    <strong>Эта ссылка не подходит</strong><br>
    Откройте страницу фильма или сериала на Кинопоиске и нажмите «Смотреть» ещё раз.
  </div>
  <script>
    window.setTimeout(function () {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.replace("https://www.kinopoisk.ru/");
      }
    }, 1500);
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    """Open KinoPoisk when the local WebView starts."""

    return redirect(KINOPOISK_START_URL, code=302)


@app.get("/mirror")
def mirror():
    """Convert the current KinoPoisk URL and redirect to KinoKino."""

    source_url = request.args.get("url", "")
    target_url = build_mirror_url(source_url)

    if target_url is not None:
        return redirect(target_url, code=302)

    return _INVALID_URL_PAGE


@app.get("/health")
def health():
    """Small local endpoint useful for diagnostics."""

    return "ok"


def install_floating_button() -> None:
    """Add the native Android button over the WebView.

    The Java helper is intentionally tiny: it only displays the button and
    passes the current URL to the Python endpoint. It is unavailable during
    desktop unit tests, so failures are logged without stopping the server.
    """

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        MirrorController = autoclass("org.kivy.android.MirrorController")
        MirrorController.install(PythonActivity.mActivity)
    except Exception:  # pragma: no cover - only reachable on Android
        print("Unable to install the floating button:", file=sys.stderr)
        traceback.print_exc()


def main() -> None:
    install_floating_button()
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        threaded=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
