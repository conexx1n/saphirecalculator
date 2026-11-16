"""Анимации уровня окна: плавная смена страниц и кросс-фейд при смене темы/акцента."""
from PySide6.QtCore import QEasingCurve, QVariantAnimation, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget

from app.styles.tokens import DUR_PAGE, DUR_THEME
from app.ui.glass import duration_of


class FadeStack(QStackedWidget):
    """QStackedWidget с плавным появлением новой страницы.

    Одна анимация на весь стек; эффект прозрачности вешается на страницу только на время
    перехода. Повторное переключение посреди анимации сразу завершает предыдущую.
    """

    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._anim = None
        self._effect = None
        self._target = None

    def set_current(self, widget):
        if widget is self.currentWidget():
            return
        self._finish()
        self.setCurrentWidget(widget)
        dur = duration_of(self._theme, DUR_PAGE)
        if dur <= 0 or not self.isVisible():
            return
        self._effect = QGraphicsOpacityEffect(widget)
        self._effect.setOpacity(0.0)
        widget.setGraphicsEffect(self._effect)
        self._target = widget
        if self._anim is None:
            self._anim = QVariantAnimation(self)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setEasingCurve(QEasingCurve.OutCubic)
            self._anim.valueChanged.connect(self._on_value)
            self._anim.finished.connect(self._finish)
        self._anim.setDuration(dur)
        self._anim.start()

    def _on_value(self, v):
        if self._effect is not None:
            self._effect.setOpacity(float(v))

    def _finish(self):
        if self._anim is not None and self._anim.state() == QVariantAnimation.Running:
            self._anim.stop()
        if self._target is not None:
            self._target.setGraphicsEffect(None)   # убираем эффект: в покое виджет рисуется напрямую
        self._effect = self._target = None

    @property
    def animating(self):
        return self._target is not None


class CrossFade(QWidget):
    """Накладка со снимком «старого» вида, которая плавно растворяется поверх нового."""

    def __init__(self, host, theme=None):
        super().__init__(host)
        self._theme, self._pix, self._opacity, self._anim = theme, None, 0.0, None
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def capture(self):
        host = self.parentWidget()
        if host is None or not host.isVisible():
            self._pix = None
            return
        self._pix = host.grab()   # если идёт предыдущий фейд — он попадёт в снимок, скачка нет

    def play(self):
        dur = duration_of(self._theme, DUR_THEME)
        if self._pix is None or dur <= 0:
            self._stop()
            return
        self.setGeometry(self.parentWidget().rect())
        self._opacity = 1.0
        self.raise_()
        self.show()
        if self._anim is None:
            self._anim = QVariantAnimation(self)
            self._anim.setStartValue(1.0)
            self._anim.setEndValue(0.0)
            self._anim.setEasingCurve(QEasingCurve.InOutQuad)
            self._anim.valueChanged.connect(self._on_value)
            self._anim.finished.connect(self._stop)
        self._anim.stop()
        self._anim.setDuration(dur)
        self._anim.start()

    def _on_value(self, v):
        self._opacity = float(v)
        self.update()

    def _stop(self):
        if self._anim is not None and self._anim.state() == QVariantAnimation.Running:
            self._anim.stop()
        self._pix = None
        self.hide()

    @property
    def running(self):
        return self.isVisible()

    def paintEvent(self, event):
        if self._pix is None:
            return
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.drawPixmap(0, 0, self._pix)
        p.end()
