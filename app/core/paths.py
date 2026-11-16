"""Platform-aware locations for Sapphire Calculator user data."""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ID = "sapphire-calculator"
APP_NAME = "Sapphire Calculator"


def _home() -> Path:
    return Path.home()


def config_dir() -> Path:
    """Return the per-user directory for settings."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", _home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = _home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", _home() / ".config"))
    return base / APP_ID


def data_dir() -> Path:
    """Return the per-user directory for databases and caches."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", _home())))
    elif sys.platform == "darwin":
        base = _home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", _home() / ".local" / "share"))
    return base / APP_ID


def legacy_data_dir() -> Path:
    """Old in-project data directory, used only to migrate existing settings."""
    return Path(__file__).resolve().parents[2] / "data"
