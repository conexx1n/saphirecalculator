"""Единая цветовая палитра (design tokens).

Palette.build(theme, accent) — единственное место, где вычисляются цвета.
Любой компонент берёт цвета из токенов палитры; акцент пересчитывает всю палитру
(фон, карточки, клавиши, поля, состояния hover/pressed/checked/disabled, ошибки).
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from PySide6.QtGui import QColor

DEFAULT_ACCENT = {"dark": "#8B7CFF", "light": "#6C5DD3"}


# ------------------------------------------------------------ цветовая математика
def mix(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(*(round(x + (y - x) * t) for x, y in zip(a.getRgb(), b.getRgb())))


def alpha(c: QColor, a: float) -> QColor:
    """Копия цвета с прозрачностью a (0..1)."""
    out = QColor(c)
    out.setAlphaF(max(0.0, min(1.0, a)))
    return out


def qss(c: QColor) -> str:
    """Цвет в синтаксисе QSS (прозрачность — в процентах)."""
    if c.alpha() == 255:
        return c.name()
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {round(c.alphaF() * 100)}%)"


def _lin(v: int) -> float:
    v /= 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def luminance(c: QColor) -> float:
    return 0.2126 * _lin(c.red()) + 0.7152 * _lin(c.green()) + 0.0722 * _lin(c.blue())


def contrast(a: QColor, b: QColor) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _readable(color: QColor, background: QColor, minimum=4.5, lighten=True) -> QColor:
    """Сдвигает светлоту цвета, пока контраст с фоном не достигнет minimum."""
    c = QColor(color)
    for _ in range(12):
        if contrast(c, background) >= minimum:
            break
        h, s, l, _a = c.getHslF()
        l = min(1.0, l + 0.06) if lighten else max(0.0, l - 0.06)
        c.setHslF(max(h, 0.0), s, l)
    return c


def _on_color(c: QColor) -> QColor:
    white, ink = QColor("#FFFFFF"), QColor("#10121A")
    return white if contrast(c, white) >= contrast(c, ink) else ink


# ------------------------------------------------------------ палитра
@dataclass(frozen=True)
class Palette:
    theme: str
    accent: QColor
    # окно
    bg_top: QColor
    bg_mid: QColor
    bg_bottom: QColor
    glow: QColor
    window_border: QColor
    # карточки
    card_hi: QColor
    card_mid: QColor
    card_lo: QColor
    card_border: QColor
    card_border_hover: QColor
    card_specular: QColor
    shadow: QColor
    # клавиши и кнопки
    key_top: QColor
    key_mid: QColor
    key_bottom: QColor
    key_border: QColor
    op_top: QColor
    op_mid: QColor
    op_bottom: QColor
    op_border: QColor
    hover_tint: QColor
    press_tint: QColor
    # акцент и его состояния
    accent_hover: QColor
    accent_pressed: QColor
    accent_soft: QColor
    accent_soft_hover: QColor
    accent_border: QColor
    accent_text: QColor
    text_on_accent: QColor
    # поля и переключатели
    field_bg: QColor
    field_border: QColor
    field_border_hover: QColor
    track_off: QColor
    knob: QColor
    menu_bg: QColor
    # текст
    text: QColor
    text_muted: QColor
    disabled_text: QColor
    disabled_bg: QColor
    # статусы
    danger: QColor
    danger_soft: QColor
    warning: QColor
    success: QColor

    @staticmethod
    def build(theme: str = "dark", accent_hex: str | None = None) -> "Palette":
        theme = "light" if theme == "light" else "dark"
        accent = QColor(accent_hex) if accent_hex and QColor(accent_hex).isValid() else QColor(DEFAULT_ACCENT[theme])
        if theme == "dark":
            return Palette._dark(accent)
        return Palette._light(accent)

    # --- тёмная тема -----------------------------------------------------
    @staticmethod
    def _dark(ac: QColor) -> "Palette":
        white, black = QColor(255, 255, 255), QColor(0, 0, 0)
        bg_mid = QColor(9, 10, 15)
        text = QColor("#F4F5FA")
        ac_text = _readable(mix(ac, white, 0.35), bg_mid, 4.5, lighten=True)
        return Palette(
            theme="dark", accent=ac,
            bg_top=mix(QColor(18, 20, 35), ac, 0.22), bg_mid=bg_mid, bg_bottom=mix(QColor(25, 15, 30), ac, 0.22),
            glow=alpha(ac, 0.16), window_border=alpha(white, 0.10),
            card_hi=alpha(white, 0.14), card_mid=alpha(white, 0.04), card_lo=alpha(black, 0.08),
            card_border=alpha(white, 0.15), card_border_hover=alpha(mix(white, ac, 0.4), 0.30),
            card_specular=alpha(white, 0.28), shadow=alpha(black, 0.60),
            key_top=alpha(white, 0.15), key_mid=alpha(white, 0.05), key_bottom=alpha(black, 0.10),
            key_border=alpha(white, 0.20),
            op_top=alpha(ac, 0.35), op_mid=alpha(ac, 0.15), op_bottom=alpha(black, 0.20), op_border=alpha(ac, 0.50),
            hover_tint=alpha(white, 0.10), press_tint=alpha(black, 0.28),
            accent_hover=mix(ac, white, 0.14), accent_pressed=mix(ac, black, 0.22),
            accent_soft=alpha(ac, 0.30), accent_soft_hover=alpha(ac, 0.42), accent_border=ac,
            accent_text=ac_text, text_on_accent=_on_color(ac),
            field_bg=alpha(white, 0.06), field_border=alpha(white, 0.12), field_border_hover=alpha(white, 0.28),
            track_off=alpha(white, 0.18), knob=QColor("#FFFFFF"), menu_bg=QColor(17, 18, 27),
            text=text, text_muted=mix(text, bg_mid, 0.42), disabled_text=alpha(text, 0.35), disabled_bg=alpha(white, 0.03),
            danger=QColor("#FF6B7A"), danger_soft=alpha(QColor("#FF6B7A"), 0.18),
            warning=QColor("#FFC857"), success=QColor("#5EE6A8"),
        )

    # --- светлая тема ----------------------------------------------------
    @staticmethod
    def _light(ac: QColor) -> "Palette":
        white, black = QColor(255, 255, 255), QColor(0, 0, 0)
        bg_mid = QColor(232, 234, 244)
        text = QColor("#14161F")
        ac_text = _readable(mix(ac, black, 0.15), white, 4.5, lighten=False)
        return Palette(
            theme="light", accent=ac,
            bg_top=mix(QColor(244, 245, 252), ac, 0.14), bg_mid=bg_mid, bg_bottom=mix(QColor(238, 232, 246), ac, 0.16),
            glow=alpha(ac, 0.14), window_border=alpha(black, 0.10),
            card_hi=alpha(white, 0.80), card_mid=alpha(white, 0.45), card_lo=alpha(white, 0.28),
            card_border=alpha(black, 0.10), card_border_hover=alpha(ac, 0.45),
            card_specular=alpha(white, 0.95), shadow=alpha(QColor(40, 40, 80), 0.28),
            key_top=alpha(white, 0.85), key_mid=alpha(white, 0.55), key_bottom=alpha(white, 0.35),
            key_border=alpha(black, 0.12),
            op_top=alpha(ac, 0.34), op_mid=alpha(ac, 0.18), op_bottom=alpha(ac, 0.10), op_border=alpha(ac, 0.55),
            hover_tint=alpha(white, 0.55), press_tint=alpha(black, 0.10),
            accent_hover=mix(ac, white, 0.12), accent_pressed=mix(ac, black, 0.18),
            accent_soft=alpha(ac, 0.22), accent_soft_hover=alpha(ac, 0.32), accent_border=ac,
            accent_text=ac_text, text_on_accent=_on_color(ac),
            field_bg=alpha(white, 0.60), field_border=alpha(black, 0.12), field_border_hover=alpha(black, 0.28),
            track_off=alpha(black, 0.20), knob=QColor("#FFFFFF"), menu_bg=QColor(246, 247, 252),
            text=text, text_muted=mix(text, white, 0.45), disabled_text=alpha(text, 0.35), disabled_bg=alpha(black, 0.04),
            danger=QColor("#D6334A"), danger_soft=alpha(QColor("#D6334A"), 0.14),
            warning=QColor("#B97A00"), success=QColor("#13845A"),
        )

    def tokens(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self) if isinstance(getattr(self, f.name), QColor)}
