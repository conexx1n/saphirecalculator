import json
import os
import re

import pytest
from PySide6.QtGui import QColor

from app.core.settings import Settings
from app.styles.manager import ThemeManager
from app.styles.palette import DEFAULT_ACCENT, Palette, contrast
from app.styles.theme import build_stylesheet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENTS = ["#8B7CFF", "#ff0004", "#ffee00", "#00b3ff", "#222222", "#ffffff", "#13ff8a"]


def test_default_accent_per_theme():
    assert Palette.build("dark").accent.name().lower() == DEFAULT_ACCENT["dark"].lower()
    assert Palette.build("light").accent.name().lower() == DEFAULT_ACCENT["light"].lower()
    assert Palette.build("dark", "not-a-color").accent.name().lower() == DEFAULT_ACCENT["dark"].lower()


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_accent_recolors_the_whole_palette(theme):
    a, b = Palette.build(theme, "#ff0004"), Palette.build(theme, "#00b3ff")
    changed = {k for k, v in a.tokens().items() if v != b.tokens()[k]}
    # фон, свечение, карточки (рамка при hover), клавиши-операторы, акцентные состояния, переключатели
    for token in ("accent", "bg_top", "bg_bottom", "glow", "card_border_hover", "op_top", "op_mid", "op_border",
                  "accent_hover", "accent_pressed", "accent_soft", "accent_soft_hover", "accent_border", "accent_text"):
        assert token in changed, token
    # нейтральные токены от акцента не зависят
    for token in ("text", "danger", "success", "field_bg", "key_top", "key_border"):
        assert token not in changed, token


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("accent", ACCENTS)
def test_text_is_readable_for_any_accent(theme, accent):
    p = Palette.build(theme, accent)
    surface = QColor(9, 10, 15) if theme == "dark" else QColor("#ffffff")
    assert contrast(p.accent_text, surface) >= 4.4
    assert contrast(p.text_on_accent, p.accent) >= 4.4
    assert contrast(p.text, surface) >= 7


def test_dark_and_light_are_really_different():
    d, l = Palette.build("dark"), Palette.build("light")
    assert d.text != l.text and d.bg_mid != l.bg_mid and d.key_top != l.key_top
    assert d.bg_mid.lightness() < 60 < 150 < l.bg_mid.lightness()


def test_stylesheet_is_generated_only_from_the_palette():
    red = build_stylesheet(Palette.build("dark", "#ff0004")).lower()
    assert "#ff0004" in red and "#8b7cff" not in red       # старый фиолетовый больше нигде не «зашит»
    violet = build_stylesheet(Palette.build("dark")).lower()
    assert "#8b7cff" in violet and "#ff0004" not in violet


def test_manager_applies_persists_and_notifies(qapp, tmp_path):
    path = str(tmp_path / "config.json")
    s = Settings(path)
    tm = ThemeManager(s, qapp)
    events = []
    tm.aboutToChange.connect(lambda: events.append(("before", tm.palette.accent.name())))
    tm.changed.connect(lambda: events.append(("after", tm.palette.accent.name())))

    tm.set_accent("#ff7a45")
    assert events == [("before", DEFAULT_ACCENT["dark"].lower()), ("after", "#ff7a45")]
    assert tm.palette.accent.name() == "#ff7a45"
    assert "#ff7a45" in qapp.styleSheet().lower()
    assert json.load(open(path))["accent"] == "#ff7a45"       # сохранено в config.json

    tm.set_accent("#ff7a45")                                  # то же значение — без лишней перерисовки
    assert len(events) == 2

    tm.set_theme("light")
    assert tm.palette.theme == "light" and json.load(open(path))["theme"] == "light"

    # «перезапуск»: новый Settings + новый ThemeManager восстанавливают всё
    tm2 = ThemeManager(Settings(path), qapp)
    assert tm2.palette.accent.name() == "#ff7a45" and tm2.palette.theme == "light"


def test_animation_setting_controls_durations(qapp, tmp_path):
    s = Settings(str(tmp_path / "c.json"))
    tm = ThemeManager(s, qapp)
    assert tm.duration(200) == 200
    s.set("animations", False)
    assert tm.duration(200) == 0


def test_no_hardcoded_colors_in_components():
    """Все цвета — только в app/styles/palette.py. Компоненты берут их из палитры."""
    pattern = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|(?<![\w.])rgba?\(|QColor\(\s*[\d\"']|Qt\.(red|green|blue|white|black|gray)\b")
    offenders = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "app")):
        if os.sep + "styles" in base or "__pycache__" in base:
            continue
        for f in files:
            if f.endswith(".py"):
                for n, line in enumerate(open(os.path.join(base, f), encoding="utf-8"), 1):
                    if pattern.search(line):
                        offenders.append(f"{f}:{n}: {line.strip()}")
    assert not offenders, "\n".join(offenders)
