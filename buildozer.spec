[app]

title = KinoKino
package.name = kinokino
package.domain = org.kinokino

source.dir = .
source.include_exts = py
source.exclude_dirs = tests,.github,.buildozer,bin,__pycache__,templates

requirements = python3,flask,requests

version = 0.2.0
orientation = all
fullscreen = 0

# Own catalog/search interface runs in Flask inside the WebView bootstrap.
# No Kivy, no custom Java helper needed.
android.permissions = INTERNET
android.allow_backup = False
android.minapi = 24
android.api = 36
android.ndk = 29
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

# Local HTML/CSS/JS interface served by Flask.
android.add_assets = templates:templates

# Use python-for-android's WebView bootstrap instead of the Kivy/SDL one.
p4a.fork = kivy
p4a.branch = develop
p4a.bootstrap = webview
p4a.port = 5000

[buildozer]

log_level = 2
warn_on_root = 1
