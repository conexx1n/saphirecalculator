#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || { echo "Python 3 is required" >&2; exit 1; }

"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests -q

pyinstaller --noconfirm --clean --windowed --onedir \
  --name SapphireCalculator \
  --collect-all PySide6 \
  --hidden-import=requests \
  --icon assets/sapphire-calculator.png \
  main.py

mkdir -p dist
cp assets/sapphire-calculator.svg dist/SapphireCalculator.svg
cp packaging/linux/sapphire-calculator.desktop dist/SapphireCalculator.desktop

echo
echo "Build complete: dist/SapphireCalculator/SapphireCalculator"
echo "To install for the current user, run: ./install_linux.sh"
