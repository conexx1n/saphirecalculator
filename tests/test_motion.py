import pytest
from PySide6.QtCore import Qt, QVariantAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget
from PySide6.QtTest import QTest

from app.ui.controls import GlassButton, ToggleSwitch
from app.ui.motion import CrossFade, FadeStack
from tests.conftest import wait_until


def anims(widget):
    return widget.findChildren(QVariantAnimation)


def test_button_has_at_most_one_level_animation_even_after_many_interactions(qapp, theme):
    b = GlassButton("7", "key", theme)
    b.resize(80, 60); b.show()
    assert anims(b) == []                         # до взаимодействия анимаций нет (ленивое создание)
    for _ in range(30):
        QTest.mousePress(b, Qt.LeftButton)
        QTest.mouseRelease(b, Qt.LeftButton)
    assert len(anims(b)) <= 1


def test_button_hover_and_press_levels_reach_targets(qapp, theme):
    b = GlassButton("7", "key", theme)
    b.show()
    b._go(1.0)
    assert wait_until(lambda: b._level == pytest.approx(1.0), qapp)
    b._go(2.0)
    assert wait_until(lambda: b._level == pytest.approx(2.0), qapp)
    b._go(0.0)
    assert wait_until(lambda: b._level == pytest.approx(0.0), qapp)


def test_retarget_mid_animation_does_not_jump(qapp, theme):
    b = GlassButton("7", "key", theme)
    b.show()
    b._go(1.0)
    QTest.qWait(40)
    mid = b._level
    assert 0.0 < mid < 1.0
    b._go(0.0)                                    # обратное направление посреди анимации
    qapp.processEvents()
    assert abs(b._level - mid) < 0.5              # стартует с текущего значения, без скачка
    assert wait_until(lambda: b._level == pytest.approx(0.0), qapp)
    assert len(anims(b)) == 1


def test_animations_off_means_instant_states(qapp, theme, settings):
    settings.set("animations", False)
    b = GlassButton("7", "key", theme)
    b.show()
    b._go(1.0)
    assert b._level == 1.0 and anims(b) == []
    sw = ToggleSwitch(theme); sw.show()
    sw.setChecked(True)
    assert sw._t == 1.0 and anims(sw) == []


def test_checked_state_animates_smoothly_then_settles(qapp, theme):
    b = GlassButton("Nav", "nav", theme)
    b.setCheckable(True); b.show()
    b.setChecked(True)
    assert b._chk < 1.0                            # плавно, а не мгновенно
    assert wait_until(lambda: b._chk == pytest.approx(1.0), qapp)
    b.setChecked(False)
    assert wait_until(lambda: b._chk == pytest.approx(0.0), qapp)


def test_toggle_switch(qapp, theme):
    sw = ToggleSwitch(theme); sw.show()
    assert not sw.isChecked() and sw._t == 0.0
    sw.click()
    assert sw.isChecked() and wait_until(lambda: sw._t == pytest.approx(1.0), qapp)
    sw.click(); sw.click(); sw.click()             # быстрые повторные переключения
    assert not sw.isChecked() and wait_until(lambda: sw._t == pytest.approx(0.0), qapp)
    assert len(anims(sw)) == 1


def test_fade_stack_switches_and_cleans_up_effect(qapp, theme):
    st = FadeStack(theme)
    a, b, c = QLabel("a"), QLabel("b"), QLabel("c")
    for w in (a, b, c):
        st.addWidget(w)
    st.resize(100, 100); st.show()
    st.set_current(b)
    assert st.currentWidget() is b and isinstance(b.graphicsEffect(), QGraphicsOpacityEffect)
    for w in (c, a, b, c, a, b, c):               # шквал переключений во время анимации
        st.set_current(w)
    assert st.currentWidget() is c
    assert wait_until(lambda: not st.animating, qapp)
    assert all(w.graphicsEffect() is None for w in (a, b, c))      # в покое эффекты не висят
    assert len(st.findChildren(QVariantAnimation)) == 1


def test_fade_stack_no_animation_when_disabled(qapp, theme, settings):
    settings.set("animations", False)
    st = FadeStack(theme)
    a, b = QLabel("a"), QLabel("b")
    st.addWidget(a); st.addWidget(b); st.show()
    st.set_current(b)
    assert st.currentWidget() is b and b.graphicsEffect() is None and not st.animating


def test_crossfade_plays_and_hides(qapp, theme):
    host = QWidget(); host.resize(120, 120); host.show()
    cf = CrossFade(host, theme)
    cf.capture(); cf.play()
    assert cf.running
    cf.capture(); cf.play()                        # повтор посреди фейда — без ошибок
    assert wait_until(lambda: not cf.running, qapp)


def test_crossfade_skipped_when_animations_off(qapp, theme, settings):
    settings.set("animations", False)
    host = QWidget(); host.resize(120, 120); host.show()
    cf = CrossFade(host, theme)
    cf.capture(); cf.play()
    assert not cf.running
