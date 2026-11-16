import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture
def settings(tmp_path):
    from app.core.settings import Settings
    return Settings(str(tmp_path / "config.json"))


@pytest.fixture
def theme(qapp, settings):
    from app.styles.manager import ThemeManager
    return ThemeManager(settings, qapp)


class FakeService:
    """Подмена CurrencyService: без сети и диска."""

    def __init__(self, rates=None, fresh=True, source="live", ok=True):
        self.rates = rates or {"USD": 1.0, "EUR": 0.5, "RUB": 100.0, "JPY": 150.0}
        self.updated_at = time.time()
        self.source, self._fresh, self.error, self._ok = source, fresh, "", ok
        self.fetch_calls = 0

    @property
    def is_fresh(self):
        return self._fresh

    def fetch(self, force=False):
        self.fetch_calls += 1
        if self._ok:
            self._fresh, self.source = True, "live"
        return self._ok


def wait_until(cond, qapp, timeout=3.0):
    from PySide6.QtTest import QTest
    end = time.time() + timeout
    while time.time() < end:
        qapp.processEvents()
        if cond():
            return True
        QTest.qWait(10)
    return cond()
