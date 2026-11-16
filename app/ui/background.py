from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QGraphicsBlurEffect, QGraphicsPixmapItem, QGraphicsScene

from app.styles.palette import alpha
from app.styles.tokens import BG_BLUR_RADIUS


def render_background(pal, w, h, blur=BG_BLUR_RADIUS, direction="diagonal") -> QPixmap:
    """Фон окна: глубокий градиент + мягкие акцентные блики, размытый один раз.

    Источник рисуется с запасом m по краям, чтобы размытие не «светлело» у границ.
    Вызывать нужно только при смене размера или палитры — результат кэшируется окном.
    """
    m = blur * 4
    src = QPixmap(w + 2 * m, h + 2 * m)
    p = QPainter(src)
    endpoints = {
        "diagonal": (m, m, m + w, m + h),
        "diagonal_reverse": (m + w, m, m, m + h),
        "horizontal": (m, m, m + w, m),
        "horizontal_reverse": (m + w, m, m, m),
        "vertical": (m, m, m, m + h),
        "vertical_reverse": (m, m + h, m, m),
    }
    g = QLinearGradient(*endpoints.get(direction, endpoints["diagonal"]))
    g.setColorAt(0.0, pal.bg_top)
    g.setColorAt(0.5, pal.bg_mid)
    g.setColorAt(1.0, pal.bg_bottom)
    p.fillRect(src.rect(), QBrush(g))
    for cx, cy, rad in ((0.12, 0.04, 0.95), (0.95, 0.98, 0.85)):
        rg = QRadialGradient(m + w * cx, m + h * cy, w * rad)
        rg.setColorAt(0.0, pal.glow)
        rg.setColorAt(1.0, alpha(pal.glow, 0.0))
        p.fillRect(src.rect(), QBrush(rg))
    p.end()

    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(src)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(blur)
    effect.setBlurHints(QGraphicsBlurEffect.QualityHint)
    item.setGraphicsEffect(effect)
    scene.addItem(item)

    out = QPixmap(w, h)
    out.fill(Qt.transparent)
    p = QPainter(out)
    scene.render(p, QRectF(0, 0, w, h), QRectF(m, m, w, h))
    p.end()
    return out
