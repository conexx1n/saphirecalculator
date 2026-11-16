"""Кастомные контролы с едиными состояниями hover / pressed / checked / disabled.

У каждого контрола не более одной QVariantAnimation (создаётся лениво, при первом
взаимодействии) — повторные нажатия во время анимации просто перенацеливают её.
"""
from PySide6.QtCore import Qt, QRectF, QSize, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QPushButton, QWidget

from app.styles.palette import alpha, mix
from app.styles.tokens import (DUR_HOVER, DUR_PRESS, DUR_SWITCH, RADIUS_CONTROL, RADIUS_KEY, ROUNDED_FAMILIES)
from app.ui.glass import duration_of, palette_of

_KEYLIKE = ("key", "operator", "accent")
_FONT_PX = {"key": 17, "operator": 17, "accent": 17, "nav": 15, "default": 14, "ghost": 13, "danger_ghost": 13}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class _Animated:
    """Лениво создаваемая анимация числового значения, перенацеливаемая на лету."""

    def __init__(self, owner, setter, easing=QEasingCurve.OutCubic):
        self._owner, self._setter, self._easing, self._anim = owner, setter, easing, None

    def run(self, start, end, duration_ms):
        if duration_ms <= 0:
            if self._anim is not None:
                self._anim.stop()
            self._setter(end)
            return
        if self._anim is None:
            self._anim = QVariantAnimation(self._owner)
            self._anim.setEasingCurve(self._easing)
            self._anim.valueChanged.connect(lambda v: self._setter(float(v)))
        self._anim.stop()
        self._anim.setStartValue(float(start))
        self._anim.setEndValue(float(end))
        self._anim.setDuration(max(40, int(duration_ms)))
        self._anim.start()


class GlassButton(QPushButton):
    """kind: key | operator | accent | nav | default | ghost | danger_ghost"""

    def __init__(self, text="", kind="key", theme=None, parent=None):
        super().__init__(text, parent)
        self._kind, self._theme = kind, theme
        self._level, self._chk = 0.0, 0.0          # level: 0 покой, 1 hover, 2 pressed
        self._kbd_focus = False
        self._level_anim = _Animated(self, self._set_level)
        self._chk_anim = _Animated(self, self._set_chk)
        self._radius = RADIUS_KEY if kind in _KEYLIKE else RADIUS_CONTROL
        self._font = QFont()
        self._font.setFamilies(ROUNDED_FAMILIES if kind in (*_KEYLIKE, "nav") else ["Inter", "Segoe UI", "sans-serif"])
        self._font.setPixelSize(_FONT_PX.get(kind, 14))
        if kind in ("accent",):
            self._font.setWeight(QFont.DemiBold)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus if kind in (*_KEYLIKE, "ghost", "danger_ghost") else Qt.TabFocus)
        self.toggled.connect(self._on_toggled)
        if theme is not None:
            theme.changed.connect(self.update)

    # --- состояние ------------------------------------------------------
    def _set_level(self, v):
        self._level = v
        self.update()

    def _set_chk(self, v):
        self._chk = v
        self.update()

    def _go(self, target):
        dur = duration_of(self._theme, DUR_PRESS if target == 2 else DUR_HOVER)
        self._level_anim.run(self._level, target, dur * abs(target - self._level))

    def _on_toggled(self, checked):
        target = 1.0 if checked else 0.0
        dur = duration_of(self._theme, int(DUR_HOVER * 1.4)) if self.isVisible() else 0
        self._chk_anim.run(self._chk, target, dur)

    def set_checked_visual(self, checked):
        """Синхронизирует визуальное состояние при программной смене выбора.

        setChecked() под QSignalBlocker не испускает toggled, поэтому без этого
        метода старый выбранный пункт мог навсегда сохранить акцентный градиент.
        """
        if self._chk_anim._anim is not None:
            self._chk_anim._anim.stop()
        self._chk = 1.0 if checked else 0.0
        self.update()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._kbd_focus = e.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.ShortcutFocusReason)
        self.update()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self._kbd_focus = False
        self.update()

    def enterEvent(self, e):
        super().enterEvent(e)
        self._go(1.0)

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._go(0.0)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton and self.isEnabled():
            self._go(2.0)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._go(1.0 if self.underMouse() else 0.0)

    # --- размеры --------------------------------------------------------
    def sizeHint(self):
        fm = QFontMetrics(self._font)
        pad = 24 if self._kind in _KEYLIKE else 28
        return QSize(fm.horizontalAdvance(self.text()) + pad, 40)

    def minimumSizeHint(self):
        return self.sizeHint()

    # --- отрисовка ------------------------------------------------------
    def _colors(self, pal):
        k = self._kind
        if k == "operator":
            top, mid, bot, border, text = pal.op_top, pal.op_mid, pal.op_bottom, pal.op_border, pal.accent_text
        elif k == "accent":
            top, mid, bot, border, text = pal.accent_hover, pal.accent, pal.accent_pressed, pal.accent_hover, pal.text_on_accent
        elif k in ("ghost", "danger_ghost"):
            top, mid, bot, border, text = pal.key_mid, pal.key_mid, pal.key_mid, pal.key_border, pal.text
        else:
            top, mid, bot, border, text = pal.key_top, pal.key_mid, pal.key_bottom, pal.key_border, pal.text
            if k in ("nav", "default") and self._chk > 0:   # анимированное состояние checked
                top, mid, bot = mix(top, pal.op_top, self._chk), mix(mid, pal.op_mid, self._chk), mix(bot, pal.op_bottom, self._chk)
                border, text = mix(border, pal.accent_border, self._chk), mix(text, pal.accent_text, self._chk)
        return top, mid, bot, border, text

    def paintEvent(self, event):
        pal = palette_of(self._theme)
        top, mid, bot, border, text = self._colors(pal)
        level = max(self._level, 1.7) if self.isDown() else self._level
        hover, press = _clamp(level), _clamp(level - 1.0)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.45)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        r = self._radius
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        g = QLinearGradient(0, rect.top(), 0, rect.bottom())
        g.setColorAt(0.0, top)
        g.setColorAt(0.5, mid)
        g.setColorAt(1.0, bot)
        p.fillPath(path, QBrush(g))
        if hover > 0 and self._kind != "danger_ghost":
            p.fillPath(path, alpha(pal.hover_tint, pal.hover_tint.alphaF() * hover))
        if self._kind == "danger_ghost" and hover > 0:
            p.fillPath(path, alpha(pal.danger, 0.55 * hover))
            border, text = mix(border, pal.danger, hover), mix(text, pal.text, hover)
        if press > 0:
            p.fillPath(path, alpha(pal.press_tint, pal.press_tint.alphaF() * press))

        if self._kind in _KEYLIKE:   # тонкий блик по верхней кромке
            hl = QLinearGradient(rect.left() + r, 0, rect.right() - r, 0)
            hl.setColorAt(0.0, alpha(pal.card_specular, 0.0))
            hl.setColorAt(0.5, alpha(pal.card_specular, 0.45))
            hl.setColorAt(1.0, alpha(pal.card_specular, 0.0))
            p.setPen(QPen(QBrush(hl), 1.0))
            p.drawLine(rect.left() + r, rect.top() + 1.2, rect.right() - r, rect.top() + 1.2)

        accent_border = mix(border, pal.accent_border, 0.85 * hover) if self._kind != "danger_ghost" else border
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(accent_border, 1.0))
        p.drawPath(path)

        if self.hasFocus() and self._kbd_focus:
            p.setPen(QPen(pal.accent, 2.0))
            p.drawRoundedRect(rect.adjusted(-0.5, -0.5, 0.5, 0.5), r, r)

        p.setPen(text)
        p.setFont(self._font)
        p.drawText(self.rect().adjusted(0, int(press), 0, int(press)), Qt.AlignCenter, self.text())
        p.end()


class ToggleSwitch(QAbstractButton):
    """Анимированный переключатель (дорожка плавно меняет цвет, ползунок едет)."""

    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self._theme, self._t = theme, 0.0
        self._anim = _Animated(self, self._set_t)
        self._kbd_focus = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self.toggled.connect(self._on_toggled)
        if theme is not None:
            theme.changed.connect(self.update)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._kbd_focus = e.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.ShortcutFocusReason)
        self.update()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self._kbd_focus = False
        self.update()

    def _set_t(self, v):
        self._t = v
        self.update()

    def _on_toggled(self, checked):
        dur = duration_of(self._theme, DUR_SWITCH) if self.isVisible() else 0
        self._anim.run(self._t, 1.0 if checked else 0.0, dur)

    def sizeHint(self):
        return QSize(46, 26)

    def paintEvent(self, event):
        pal = palette_of(self._theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.45)
        track = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(Qt.NoPen)
        p.setBrush(mix(pal.track_off, pal.accent, self._t))
        p.drawRoundedRect(track, track.height() / 2, track.height() / 2)
        d = track.height() - 6
        x = track.left() + 3 + (track.width() - d - 6) * self._t
        p.setBrush(pal.knob)
        p.drawEllipse(QRectF(x, track.top() + 3, d, d))
        if self.hasFocus() and self._kbd_focus:
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(pal.accent, 2.0))
            p.drawRoundedRect(track.adjusted(-1, -1, 1, 1), track.height() / 2 + 1, track.height() / 2 + 1)
        p.end()


class ColorSwatch(QWidget):
    """Квадратик с текущим акцентным цветом."""

    def __init__(self, theme=None, size=34, parent=None):
        super().__init__(parent)
        self._theme = theme
        self.setFixedSize(size, size)
        if theme is not None:
            theme.changed.connect(self.update)

    def paintEvent(self, event):
        pal = palette_of(self._theme)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setBrush(pal.accent)
        p.setPen(QPen(pal.card_border_hover, 1.0))
        p.drawRoundedRect(rect, RADIUS_CONTROL, RADIUS_CONTROL)
        p.end()
