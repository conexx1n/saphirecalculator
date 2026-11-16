from PySide6.QtCore import Qt, QRectF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect

from app.styles.palette import Palette, alpha, mix
from app.styles.tokens import DUR_HOVER, RADIUS_CARD

_DEFAULT = {}


def palette_of(theme) -> Palette:
    """Палитра менеджера темы или тёмная по умолчанию (для виджетов без менеджера)."""
    if theme is not None:
        return theme.palette
    if "dark" not in _DEFAULT:
        _DEFAULT["dark"] = Palette.build("dark")
    return _DEFAULT["dark"]


def repolish(widget):
    """Перечитать QSS после смены динамического свойства (property)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def duration_of(theme, ms):
    return theme.duration(ms) if theme is not None else ms


class GlassCard(QFrame):
    """Полупрозрачная «стеклянная» поверхность: градиент, блик по верхней кромке,
    рамка, мягкая тень. Все цвета — из палитры. Плавная подсветка при наведении."""

    def __init__(self, parent=None, *, theme=None, radius=RADIUS_CARD):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setFrameShape(QFrame.NoFrame)
        self._theme, self._radius = theme, radius
        self._hover, self._anim = 0.0, None

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(30)
        self._shadow.setOffset(0, 8)
        self.setGraphicsEffect(self._shadow)
        self._sync_theme()
        if theme is not None:
            theme.changed.connect(self._sync_theme)

    def _sync_theme(self):
        self._shadow.setColor(palette_of(self._theme).shadow)
        self.update()

    # --- плавная подсветка рамки ---------------------------------------
    def _go(self, target):
        dur = duration_of(self._theme, DUR_HOVER * 2)
        if dur <= 0:
            self._hover = target
            self.update()
            return
        if self._anim is None:
            self._anim = QVariantAnimation(self)
            self._anim.setEasingCurve(QEasingCurve.OutCubic)
            self._anim.valueChanged.connect(self._on_hover)
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(float(target))
        self._anim.setDuration(dur)
        self._anim.start()

    def _on_hover(self, v):
        self._hover = float(v)
        self.update()

    def enterEvent(self, e):
        super().enterEvent(e)
        self._go(1.0)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._go(0.0)

    def paintEvent(self, event):
        pal = palette_of(self._theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        r = self._radius

        g = QLinearGradient(rect.topLeft(), rect.bottomRight())
        g.setColorAt(0.0, pal.card_hi)
        g.setColorAt(0.5, pal.card_mid)
        g.setColorAt(1.0, pal.card_lo)
        p.setBrush(QBrush(g))
        p.setPen(QPen(mix(pal.card_border, pal.card_border_hover, self._hover), 1.2))
        p.drawRoundedRect(rect, r, r)

        # блик вдоль верхней кромки
        hl = QLinearGradient(rect.left() + r, 0, rect.right() - r, 0)
        hl.setColorAt(0.0, alpha(pal.card_specular, 0.0))
        hl.setColorAt(0.5, pal.card_specular)
        hl.setColorAt(1.0, alpha(pal.card_specular, 0.0))
        p.setPen(QPen(QBrush(hl), 1.0))
        p.drawLine(rect.left() + r, rect.top() + 1.2, rect.right() - r, rect.top() + 1.2)
        p.end()
