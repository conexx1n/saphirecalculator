# Sapphire Calculator

**Настольный калькулятор и конвертер на Python + PySide6**




<img width="462" height="700" alt="изображение" src="https://github.com/user-attachments/assets/54beaf0b-effc-457f-91d1-c6a1b5dac277" />


**Sapphire Calculator** — настольный калькулятор и конвертер на PySide6 с мягким размытым градиентным фоном, полупрозрачными карточками и настраиваемыми цветовыми темами

[English](#english)

## Возможности

- Калькулятор с обработкой математических выражений
- Конвертер валют и единиц: длина, масса, данные, температура, скорость, объём, время и площадь
- Автоматический пересчёт при изменении значения или единиц
- Светлая и тёмная темы, настраиваемый акцентный цвет
- Русский и английский интерфейс
- Анимации и настройки внешнего вида
- История вычислений на SQLite
- Курсы валют с сетевым обновлением, локальным кэшем и резервными значениями
- Перетаскиваемое окно без стандартной рамки

## Скриншоты

Скриншоты интерфейса пока не добавлены

## Требования

- Python 3.10 или новее
- Windows 10/11 или Linux с графическим окружением
- Для запуска из исходников: PySide6 и requests

## Запуск из исходников

### Linux (bash / zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### Linux (fish)

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Тесты

```bash
python -m pytest tests -q
```

Тесты Qt используют `QT_QPA_PLATFORM=offscreen`, поэтому для них не требуется открывать окно приложения

## Сборка

### Windows

Запусти `build_windows.bat`. Результат появится в `dist/SapphireCalculator/`. Для создания установщика открой `installer/SapphireCalculator.iss` в [Inno Setup](https://jrsoftware.org/isinfo.php) после сборки

### Linux

```bash
chmod +x build_linux.sh install_linux.sh uninstall_linux.sh
./build_linux.sh
./install_linux.sh
```

Сборка создаёт автономную папку `dist/SapphireCalculator/`. Установка копирует её в `~/.local/opt`, добавляет команду `sapphire-calculator` и ярлык в меню приложений KDE/других совместимых окружений. Удаление приложения: `./uninstall_linux.sh`

PyInstaller включает интерпретатор Python и необходимые зависимости в сборку. На компьютере конечного пользователя отдельно устанавливать Python не требуется. Сборки Windows и Linux нужно выполнять на соответствующей операционной системе

## Где хранятся настройки и данные

Пользовательские настройки, история и кэш курсов сохраняются вне папки программы:

- Linux: `~/.config/sapphire-calculator` и `~/.local/share/sapphire-calculator`
- Windows: `%APPDATA%\sapphire-calculator` и `%LOCALAPPDATA%\sapphire-calculator`
- macOS: `~/Library/Application Support/sapphire-calculator`

Это позволяет обновлять или переустанавливать приложение без удаления пользовательских настроек и истории. Скрипт удаления Linux удаляет файлы приложения, но оставляет пользовательские данные

## Структура проекта

```text
app/
  core/       вычисления, конвертация, настройки, пути, история и курсы
  styles/     цветовая палитра и темы
  ui/         главное окно, страницы, компоненты и анимации
assets/       иконки приложения
installer/    сценарий установщика Windows (Inno Setup)
packaging/    метаданные Linux-приложения
 tests/       автоматические тесты
main.py       точка входа
```

## Лицензия и дизайн

Исходный код распространяется по лицензии MIT. См. файл [LICENSE](LICENSE)

Дизайн-подход вдохновлён Unslop by Damir Sokolovsky (CC BY 4.0); также использовался Design Studio UI/UX workflow

---

## English

Sapphire Calculator is a PySide6 desktop calculator and unit converter featuring a softly blurred gradient background, translucent cards and customizable color themes

### Features

- Mathematical expression calculator
- Currency and unit conversion: length, mass, data, temperature, speed, volume, time and area
- Automatic recalculation when values or units change
- Light and dark themes with an adjustable accent color
- Russian and English interface
- UI animations and appearance settings
- SQLite calculation history
- Currency rates with online updates, local cache and fallback values
- Frameless, draggable application window

See the sections above for setup, tests, build instructions and data locations
