# KinoKino for Android

Обёртка над мобильным сайтом Кинопоиска с висячей кнопкой **«Смотреть»** справа.

Кнопка преобразует текущую ссылку Кинопоиска вида

```text
https://www.kinopoisk.ru/<тип>/<числовой-id>/
```

в ссылку

```text
https://www.kinokino.win/<тип>/<числовой-id>/
```

и открывает её в том же WebView. Если открытая страница не соответствует формату, приложение показывает сообщение и возвращается назад.

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

- `main.py` — локальный Flask-сервер и маршрут преобразования ссылки.
- `url_rules.py` — строгая проверка и преобразование URL.
- `java/org/kivy/android/MirrorController.java` — небольшой Android-слой для висячей кнопки поверх WebView.
- `buildozer.spec` — настройки Android-пакета.
- `.github/workflows/android.yml` — автоматические тесты и сборка APK.

Приложение использует системный Android WebView, поэтому cookies и возрастные/региональные ограничения сайтов обрабатываются средствами Android. Окончательная совместимость с конкретными страницами проверяется на физическом устройстве.
