"""Курсы валют: кэш на диске, валидация ответа API, резервные курсы.

Сервис синхронный и не зависит от Qt. В GUI его вызывают из фонового потока
(см. app/ui/workers.py), поэтому fetch() не должен падать и не должен
оставлять объект в промежуточном состоянии.
"""
import json
import math
import os
import tempfile
import threading
import time

from app.core.paths import data_dir

CACHE_PATH = str(data_dir() / "rates.json")
CACHE_TTL = 3600          # курсы считаются свежими час
RETRY_INTERVAL = 60       # после неудачи следующая попытка не раньше, чем через минуту
API_URL = "https://open.er-api.com/v6/latest/USD"
POPULAR = ("USD", "EUR", "RUB", "GBP", "CNY", "JPY", "KZT", "UAH")

FALLBACK = {
    "USD": 1.0, "EUR": 0.92, "RUB": 92.0, "GBP": 0.79,
    "CNY": 7.25, "JPY": 155.0, "KZT": 450.0, "UAH": 41.0,
}

NAMES = {
    "USD": "US Dollar", "EUR": "Euro", "RUB": "Russian Ruble", "GBP": "British Pound",
    "CNY": "Chinese Yuan", "JPY": "Japanese Yen", "KZT": "Kazakhstani Tenge", "UAH": "Ukrainian Hryvnia",
}


def _validate(rates):
    """Оставляет только положительные конечные числа; требует наличие USD."""
    if not isinstance(rates, dict):
        raise ValueError("rates is not a dict")
    clean = {}
    for code, value in rates.items():
        if isinstance(code, str) and isinstance(value, (int, float)) and not isinstance(value, bool):
            if math.isfinite(value) and value > 0:
                clean[code] = float(value)
    if "USD" not in clean:
        raise ValueError("USD rate is missing")
    return clean


def ordered_codes(rates):
    """Популярные валюты первыми, остальные по алфавиту."""
    first = [c for c in POPULAR if c in rates]
    return first + sorted(c for c in rates if c not in POPULAR)


class CurrencyService:
    def __init__(self, cache_path=None):
        self.cache_path = cache_path or CACHE_PATH
        self.rates, self.updated_at, self.error = {}, 0.0, ""
        self.source = "fallback"          # live | cache | fallback
        self._last_failure = 0.0
        self._lock = threading.Lock()
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        except OSError:
            pass
        self._load()
        if not self.rates:                # курсы доступны всегда, даже без кэша и сети
            self.rates, self.updated_at, self.source = dict(FALLBACK), 0.0, "fallback"

    # --- состояние -------------------------------------------------------
    @property
    def is_fresh(self):
        return self.source in ("live", "cache") and (time.time() - self.updated_at) < CACHE_TTL

    # --- диск ------------------------------------------------------------
    def _load(self):
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, encoding="utf-8") as fh:
                    d = json.load(fh)
                rates = _validate(d.get("rates"))
                updated = d.get("updated_at", 0.0)
                self.rates = rates
                self.updated_at = float(updated) if isinstance(updated, (int, float)) else 0.0
                self.source = "cache"
        except Exception:  # повреждённый кэш не должен мешать запуску
            self.rates, self.updated_at = {}, 0.0

    def _save(self):
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.cache_path), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"rates": self.rates, "updated_at": self.updated_at}, fh)
            os.replace(tmp, self.cache_path)
        except Exception:
            if tmp and os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # --- сеть ------------------------------------------------------------
    def fetch(self, force=False):
        """True — курсы свежие (кэш или сеть). При ошибке сохраняются прежние курсы."""
        now = time.time()
        if not force:
            if self.is_fresh:
                return True
            if self._last_failure and now - self._last_failure < RETRY_INTERVAL:
                return False
        try:
            import requests  # импорт здесь: без пакета приложение работает офлайн
            r = requests.get(API_URL, timeout=(3, 5))
            r.raise_for_status()
            d = r.json()
            if d.get("result") != "success":
                raise RuntimeError("API failure")
            rates = _validate(d.get("rates"))
        except Exception as e:
            self.error = str(e)
            self._last_failure = now
            return False
        with self._lock:
            self.rates, self.updated_at, self.source = rates, now, "live"
            self.error, self._last_failure = "", 0.0
        self._save()
        return True

    def convert(self, amount, frm, to):
        """float-версия для совместимости; в UI используется units.convert_currency."""
        rates = self.rates
        if frm not in rates or to not in rates:
            raise ValueError(f"Unknown pair {frm}->{to}")
        return (amount / rates[frm]) * rates[to]
