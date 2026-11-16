"""Неценовые дизайн-токены: шрифты, радиусы, длительности анимаций."""

FONT_UI = '"Inter", "Segoe UI", sans-serif'
ROUNDED_FAMILIES = ["Arial Rounded MT Bold", "Varela Round", "Nunito", "Segoe UI Rounded", "Comic Sans MS", "sans-serif"]
FONT_ROUNDED = ", ".join(f'"{f}"' if " " in f else f for f in ROUNDED_FAMILIES)

RADIUS_WINDOW = 20
RADIUS_CARD = 20
RADIUS_KEY = 14
RADIUS_CONTROL = 10

BG_BLUR_RADIUS = 28

DUR_HOVER = 140      # мс
DUR_PRESS = 80
DUR_PAGE = 200
DUR_THEME = 280
DUR_SWITCH = 160
