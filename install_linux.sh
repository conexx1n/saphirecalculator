#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
APP_SOURCE="$(pwd)/dist/SapphireCalculator"
if [[ ! -x "$APP_SOURCE/SapphireCalculator" ]]; then
  echo "Build not found. Run ./build_linux.sh first." >&2
  exit 1
fi

APP_DIR="$HOME/.local/opt/SapphireCalculator"
BIN_DIR="$HOME/.local/bin"
APPLICATIONS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR" "$BIN_DIR" "$APPLICATIONS_DIR" "$ICON_DIR"
cp -a "$APP_SOURCE/." "$APP_DIR/"
ln -sfn "$APP_DIR/SapphireCalculator" "$BIN_DIR/sapphire-calculator"
install -m 644 assets/sapphire-calculator.svg "$ICON_DIR/sapphire-calculator.svg"
cat > "$APPLICATIONS_DIR/sapphire-calculator.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Sapphire Calculator
Comment=Modern desktop calculator and unit converter
Exec=$BIN_DIR/sapphire-calculator
Icon=sapphire-calculator
Terminal=false
Categories=Utility;Calculator;
StartupNotify=true
DESKTOP
chmod 644 "$APPLICATIONS_DIR/sapphire-calculator.desktop"

printf 'Installed Sapphire Calculator for the current user.\n'
printf 'If the app does not appear in KDE menu immediately, log out and back in.\n'
printf 'Launch from terminal with: sapphire-calculator\n'
