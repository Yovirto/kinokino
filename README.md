# KinoKino for Android

Приложение с собственным каталогом/поиском (публичный suggest-API Кинопоиска)
и встроенным HLS-плеером. Кнопка **«Смотреть»** открывает локальную страницу
`/watch/<id>`: приложение запрашивает список озвучек и качеств через
`stream_parser.py`, воспроизведение идёт через локальный прокси
`/stream/manifest` и `/stream/segment`, который добавляет CDN нужные
`Origin`/`Referer` заголовки.

Плеер построен на hls.js (загружается с CDN). Качество выбирается
автоматически или вручную, отдельные аудиодорожки (озвучки) подхватываются
из master-плейлиста.

**Юридическое замечание:** код реализует воспроизведение только тех потоков,
которые пользователь и так может открыть в браузере. DRM и платный доступ
не обходятся. Не используйте приложение для распространения контента, на
который у вас нет прав.

## Сборка APK через GitHub Actions

1. Создайте на GitHub новый репозиторий.
2. Загрузите в него содержимое этой папки.
3. Откройте **Actions → Build Android APK**.
4. Нажмите **Run workflow** (workflow также запускается автоматически после push в `main`).
5. После успешной сборки скачайте артефакт **KinoKino-debug-apk**.
6. Распакуйте ZIP и установите APK на Android. Для установки может потребоваться разрешение на установку из неизвестных источников.

Workflow выполняет модульные тесты и собирает универсальный debug APK для архитектур `arm64-v8a` и `armeabi-v7a`.

## Локальная сборка через WSL2

Buildozer не поддерживает нативную сборку Android в Windows, поэтому используйте WSL2 и Ubuntu:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
    automake libltdl-dev libffi-dev libssl-dev

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install buildozer==1.6.0

buildozer -v android debug
```

Готовый файл появится в каталоге `bin/`.

## Локальные тесты

```bash
python -m pip install "Flask>=3.1,<4"
python -m unittest discover -s tests -v
```

## Устройство проекта

- `main.py` — локальный Flask-сервер: интерфейс каталога, HLS-прокси и страница плеера.
- `kinopoisk_parser.py` — публичный suggest-API Кинопоиска (поиск без ключа).
- `stream_parser.py` — резолвинг провайдеров/озвучек и переписывание плейлистов.
- `templates/index.html` — интерфейс каталога и поиска.
- `templates/watch.html` — страница плеера (hls.js + выбор озвучки/качества).
- `buildozer.spec` — настройки Android-пакета.
- `.github/workflows/android.yml` — автоматические тесты и сборка APK.

Приложение использует системный Android WebView. Воспроизведение HLS
выполняется через hls.js внутри WebView; на устройствах со встроенной
поддержкой HLS используется нативный путь.
