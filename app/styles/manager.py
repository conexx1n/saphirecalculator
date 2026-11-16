from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.styles.palette import Palette
from app.styles.theme import build_stylesheet


class ThemeManager(QObject):
    """Владеет текущей палитрой. Смена темы/акцента: aboutToChange → применение → changed.

    Плавность обеспечивает окно: на aboutToChange оно снимает снимок интерфейса и
    после changed плавно растворяет его (QSS пересобирается один раз, а не на каждом кадре).
    """

    aboutToChange = Signal()
    changed = Signal()

    def __init__(self, settings, app=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.app = app if app is not None else QApplication.instance()
        self._palette = self._build()
        self._apply_qss()

    def _build(self):
        return Palette.build(self.settings.get("theme", "dark"), self.settings.get("accent"))

    @property
    def palette(self) -> Palette:
        return self._palette

    @property
    def animations(self) -> bool:
        return bool(self.settings.get("animations", True))

    def duration(self, ms: int) -> int:
        """Длительность анимации с учётом настройки «Анимации»."""
        return ms if self.animations else 0

    def set_accent(self, accent_hex):
        self.settings.set("accent", accent_hex)
        self._refresh()

    def set_theme(self, theme):
        self.settings.set("theme", "light" if theme == "light" else "dark")
        self._refresh()

    def _refresh(self):
        new = self._build()
        if new == self._palette:
            return
        self.aboutToChange.emit()
        self._palette = new
        self._apply_qss()
        self.changed.emit()

    def _apply_qss(self):
        if self.app is not None:
            self.app.setStyleSheet(build_stylesheet(self._palette))
