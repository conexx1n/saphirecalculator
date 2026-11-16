import json
import math
import os
import time

import pytest

from app.core import currency
from app.core.currency import CACHE_TTL, FALLBACK, RETRY_INTERVAL, CurrencyService, ordered_codes


class Resp:
    def __init__(self, payload, status=200):
        self._p, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        if isinstance(self._p, Exception):
            raise self._p
        return self._p


def ok_payload(**rates):
    return {"result": "success", "rates": {"USD": 1, "EUR": 0.5, **rates}}


@pytest.fixture
def cache(tmp_path):
    return str(tmp_path / "rates.json")


@pytest.fixture
def net(monkeypatch):
    """Подмена requests.get; считает обращения."""
    state = {"calls": 0, "resp": Resp(ok_payload())}

    def fake_get(url, timeout=None):
        state["calls"] += 1
        if isinstance(state["resp"], Exception):
            raise state["resp"]
        return state["resp"]

    import requests
    monkeypatch.setattr(requests, "get", fake_get)
    return state


def test_convert_cache(cache):          # прежний тест, но без обращения к реальному data/rates.json
    s = CurrencyService(cache)
    s.rates = {"USD": 1.0, "EUR": 0.5}
    assert abs(s.convert(10, "USD", "EUR") - 5.0) < 1e-9
    with pytest.raises(ValueError):
        s.convert(1, "USD", "XXX")


def test_no_cache_uses_fallback_and_is_not_fresh(cache):
    s = CurrencyService(cache)
    assert s.rates == FALLBACK and s.source == "fallback"
    assert s.updated_at == 0.0 and not s.is_fresh       # резервные курсы не выдаются за свежие


def test_loads_valid_cache(cache):
    json.dump({"rates": {"USD": 1, "EUR": 0.9}, "updated_at": time.time()}, open(cache, "w"))
    s = CurrencyService(cache)
    assert s.source == "cache" and s.rates["EUR"] == 0.9 and s.is_fresh


@pytest.mark.parametrize("content", ["{broken", "[]", '{"rates": 5}', '{"rates": {"EUR": 1}}', ""])
def test_corrupted_cache_falls_back(cache, content):
    open(cache, "w").write(content)
    s = CurrencyService(cache)
    assert s.rates == FALLBACK and s.source == "fallback"


def test_stale_cache_is_not_fresh(cache):
    json.dump({"rates": {"USD": 1, "EUR": 0.9}, "updated_at": time.time() - CACHE_TTL - 5}, open(cache, "w"))
    s = CurrencyService(cache)
    assert s.source == "cache" and not s.is_fresh


def test_fetch_success_saves_cache_atomically(cache, net):
    s = CurrencyService(cache)
    assert s.fetch() is True
    assert s.source == "live" and s.is_fresh and s.rates["EUR"] == 0.5
    assert json.load(open(cache))["rates"]["EUR"] == 0.5
    assert [f for f in os.listdir(os.path.dirname(cache)) if f.endswith(".tmp")] == []


def test_fresh_rates_do_not_hit_network(cache, net):
    s = CurrencyService(cache)
    s.fetch()
    s.fetch()
    s.fetch()
    assert net["calls"] == 1


def test_offline_keeps_previous_rates_and_backs_off(cache, net):
    json.dump({"rates": {"USD": 1, "EUR": 0.9}, "updated_at": time.time() - CACHE_TTL - 5}, open(cache, "w"))
    s = CurrencyService(cache)
    net["resp"] = ConnectionError("no internet")
    assert s.fetch() is False
    assert s.rates["EUR"] == 0.9 and s.source == "cache" and "no internet" in s.error
    assert s.fetch() is False and net["calls"] == 1           # пауза между неудачными попытками
    assert s.fetch(force=True) is False and net["calls"] == 2  # force обходит паузу
    s._last_failure = time.time() - RETRY_INTERVAL - 1
    s.fetch()
    assert net["calls"] == 3


def test_offline_without_cache_uses_fallback(cache, net):
    s = CurrencyService(cache)
    net["resp"] = ConnectionError("down")
    assert s.fetch() is False
    assert s.rates == FALLBACK and s.source == "fallback" and not s.is_fresh


@pytest.mark.parametrize("payload", [
    {"result": "error"}, {"result": "success"}, {"result": "success", "rates": []},
    {"result": "success", "rates": {"EUR": 1}},            # нет USD
    {"result": "success", "rates": {"USD": 0}},
    "garbage",
])
def test_invalid_api_payload_is_rejected(cache, net, payload):
    s = CurrencyService(cache)
    before = dict(s.rates)
    net["resp"] = Resp(payload)
    assert s.fetch() is False
    assert s.rates == before and s.source == "fallback"


def test_http_error_and_bad_json(cache, net):
    s = CurrencyService(cache)
    net["resp"] = Resp(ok_payload(), status=503)
    assert s.fetch() is False
    net["resp"] = Resp(ValueError("bad json"))
    assert s.fetch(force=True) is False


def test_garbage_values_are_filtered(cache, net):
    s = CurrencyService(cache)
    net["resp"] = Resp({"result": "success", "rates": {"USD": 1, "EUR": 0.5, "BAD": -1, "NAN": math.nan,
                                                        "INF": math.inf, "STR": "x", "BOOL": True, "ZERO": 0}})
    assert s.fetch() is True
    assert set(s.rates) == {"USD", "EUR"}


def test_ordered_codes():
    codes = ordered_codes({"ZZZ": 1, "EUR": 1, "AAA": 1, "USD": 1, "RUB": 1})
    assert codes == ["USD", "EUR", "RUB", "AAA", "ZZZ"]


def test_requests_missing_means_offline_not_crash(cache, monkeypatch):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "requests":
            raise ImportError("no requests")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    s = CurrencyService(cache)
    assert s.fetch() is False and s.rates
