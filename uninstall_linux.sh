#!/usr/bin/env bash
set -euo pipefail
rm -rf "$HOME/.local/opt/SapphireCalculator"
rm -f "$HOME/.local/bin/sapphire-calculator"
rm -f "$HOME/.local/share/applications/sapphire-calculator.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/sapphire-calculator.svg"
echo "Sapphire Calculator application files removed. User settings and history were kept."
