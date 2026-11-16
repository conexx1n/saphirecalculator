import json
import os
import re
import tempfile

from app.core.paths import config_dir, legacy_data_dir

DEFAULTS = {"theme": "dark", "accent": None, "lang": "ru", "animations": True, "gradient_direction": "diagonal"}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class Settings:
    """JSON-настройки. Устойчивы к повреждённому файлу, пишутся атомарно.

    Совместимость: если config.json ещё нет, значения подхватываются из старого
    settings.json (ключ 'language' → 'lang'); неизвестные ключи сохраняются как есть.
    """

    def __init__(self, path=None, legacy_path=None):
        if path is None:
            path = str(config_dir() / "config.json")
            if legacy_path is None:
                old_data = legacy_data_dir()
                old_config = old_data / "config.json"
                old_settings = old_data / "settings.json"
                legacy_path = str(old_config if old_config.exists() else old_settings)
        self.path = path
        self.legacy_path = legacy_path
        self.last_error = ""
        self.data = dict(DEFAULTS)
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        except OSError as e:
            self.last_error = str(e)
        self.load()

    # --- чтение ----------------------------------------------------------
    def _read(self, path):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        if not isinstance(d, dict):
            raise ValueError("settings root must be an object")
        return d

    def load(self):
        loaded, migrated = None, False
        if os.path.exists(self.path):
            try:
                loaded = self._read(self.path)
            except Exception as e:      # повреждённый файл откладываем в сторону
                self.last_error = f"corrupted settings: {e}"
                try:
                    os.replace(self.path, self.path + ".corrupt")
                except OSError:
                    pass
        elif self.legacy_path and os.path.exists(self.legacy_path):
            try:
                loaded, migrated = self._read(self.legacy_path), True
            except Exception as e:
                self.last_error = f"legacy settings unreadable: {e}"
        if loaded:
            if migrated and "lang" not in loaded and loaded.get("language") in ("ru", "en"):
                loaded["lang"] = loaded["language"]
            self.data.update(loaded)
        self._sanitize()
        if migrated:
            self.save()

    def _sanitize(self):
        d = self.data
        if d.get("theme") not in ("dark", "light"):
            d["theme"] = DEFAULTS["theme"]
        if d.get("accent") is not None and not (isinstance(d["accent"], str) and _HEX.match(d["accent"])):
            d["accent"] = None
        if d.get("lang") not in ("ru", "en"):
            d["lang"] = DEFAULTS["lang"]
        if not isinstance(d.get("animations"), bool):
            d["animations"] = DEFAULTS["animations"]
        if d.get("gradient_direction") not in ("diagonal", "diagonal_reverse", "horizontal", "horizontal_reverse", "vertical", "vertical_reverse"):
            d["gradient_direction"] = "diagonal"

    # --- запись ----------------------------------------------------------
    def save(self):
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path) or ".", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
            self.last_error = ""
        except Exception as e:
            self.last_error = str(e)
            if tmp and os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    def get(self, k, d=None):
        return self.data.get(k, d)

    def set(self, k, v):
        self.data[k] = v
        self.save()
