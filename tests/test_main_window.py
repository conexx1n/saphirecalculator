import json
import os
import subprocess
import sys

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QVariantAnimation
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QColorDialog, QGraphicsEffect, QPushButton, QWidget
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from app.core import i18n
from app.core.settings import Settings
from app.styles.manager import ThemeManager
from app.ui.main_window import MainWindow
from tests.conftest import FakeService, wait_until

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def win(qapp, tmp_path):
    i18n.set_lang("ru")
    s = Settings(str(tmp_path / "config.json"))
    w = MainWindow(s, ThemeManager(s, qapp), currency_service=FakeService())
    w.show()
    qapp.processEvents()
    yield w
    w.close()
    i18n.set_lang("ru")


def keys(w, *items):
    for it in items:
        QTest.keyClicks(w, it) if isinstance(it, str) else QTest.keyClick(w, it)


def mouse(widget, typ, gpos, btn=Qt.LeftButton, buttons=Qt.LeftButton):
    QWidget.window(widget)  # noqa: B018 (проверяем, что виджет жив)
    ev = QMouseEvent(typ, QPointF(4, 4), QPointF(gpos), btn, buttons, Qt.NoModifier)
    from PySide6.QtWidgets import QApplication
    QApplication.sendEvent(widget, ev)


# ---------------------------------------------------------------- запуск и страницы
def test_starts_on_calculator(win):
    assert win.stack.currentWidget() is win.calc_panel
    assert [b.isChecked() for b in (win.btn_calc, win.btn_conv, win.btn_settings)] == [True, False, False]
    assert win.converter is None                       # конвертер создаётся лениво (и не грузит сеть при старте)


def test_one_window_three_pages_switching(win, qapp):
    win.btn_conv.click()
    assert win.stack.currentWidget() is win.converter and win.btn_conv.isChecked() and not win.btn_calc.isChecked()
    win.btn_settings.click()
    assert win.stack.currentWidget() is win.settings_panel and win.btn_settings.isChecked()
    win.btn_calc.click()
    assert win.stack.currentWidget() is win.calc_panel and win.btn_calc.isChecked()
    assert len(QApplication_top_levels(win)) == 1       # нет отдельных окон конвертера/настроек


def QApplication_top_levels(win):
    from PySide6.QtWidgets import QApplication
    return [w for w in QApplication.topLevelWidgets() if w.isVisible() and w.parent() is None and isinstance(w, MainWindow)]


def test_rapid_page_switching_is_stable(win, qapp):
    win.btn_conv.click()
    for i in range(40):
        (win.btn_calc, win.btn_settings, win.btn_conv)[i % 3].click()
    final = (win.btn_calc, win.btn_settings, win.btn_conv)[39 % 3]
    assert win.stack.currentWidget() is {win.btn_calc: win.calc_panel, win.btn_settings: win.settings_panel, win.btn_conv: win.converter}[final]
    assert wait_until(lambda: not win.stack.animating, qapp)
    assert all(win.stack.widget(i).graphicsEffect() is None for i in range(win.stack.count()))


def test_converter_categories_live_inside_page(win):
    win.show_converter()
    assert len(win.converter.category_buttons) == 9
    assert not win.menuBar().actions()                 # нет дублирующего меню категорий
    win.converter.category_buttons["temperature"].click()
    assert win.stack.currentWidget() is win.converter and win.converter.ctype == "temperature"
    assert win.converter.category_buttons["temperature"].isChecked()
    win.converter.category_buttons["area"].click()
    assert win.converter.ctype == "area" and win.converter.title_lbl.text() == "Площадь"
    assert win.converter.result.text() not in ("", "—")


def test_converter_page_autocalculates_inside_window(win):
    win.show_converter()
    win.converter.set_type("mass", "Масса")
    win.converter.input.setText("2")
    win.converter.from_combo.setCurrentIndex(win.converter.from_combo.findData("t"))
    win.converter.to_combo.setCurrentIndex(win.converter.to_combo.findData("kg"))
    assert win.converter.result.text() == "2000"


# ---------------------------------------------------------------- калькулятор и клавиатура
def test_calculator_buttons(win):
    for label in ("2", "+", "3", "×", "4", "="):
        win.calc_panel.buttons[label].click()
    assert win.calc_panel.display.text() == "2+3*4" and win.calc_panel.result_label.text() == "14"
    win.calc_panel.buttons["AC"].click()
    assert win.calc_panel.display.text() == "" and win.calc_panel.result_label.text() == "0"
    for label in ("√", "9", ")", "="):
        win.calc_panel.buttons[label].click()
    assert win.calc_panel.result_label.text() == "3"


def test_keyboard_matches_buttons(win):
    keys(win, "12+3*4")
    assert win.calc_panel.display.text() == "12+3*4"
    keys(win, Qt.Key_Backspace)
    assert win.calc_panel.display.text() == "12+3*"
    keys(win, "5", Qt.Key_Return)
    assert win.calc_panel.result_label.text() == "27"
    keys(win, Qt.Key_Escape)
    assert win.calc_panel.display.text() == "" and win.calc_panel.result_label.text() == "0"
    keys(win, "7/2", Qt.Key_Enter)
    assert win.calc_panel.result_label.text() == "3.5"
    keys(win, Qt.Key_Escape)
    keys(win, "1,5+(2)%^abc")                           # запятая → точка, буквы игнорируются
    assert win.calc_panel.display.text() == "1.5+(2)%^"


def test_keyboard_after_clicking_a_button_still_reaches_calculator(win):
    win.calc_panel.buttons["8"].click()
    QTest.mouseClick(win.calc_panel.buttons["8"], Qt.LeftButton)
    keys(win, "+2", Qt.Key_Return)
    assert win.calc_panel.display.text() == "88+2" and win.calc_panel.result_label.text() == "90"


def test_error_state_and_recovery(win):
    keys(win, "5/0", Qt.Key_Return)
    assert win.calc_panel.result_label.text() == "Ошибка" and win.calc_panel.result_label.property("error") is True
    keys(win, Qt.Key_Escape, "2+2", Qt.Key_Return)
    assert win.calc_panel.result_label.text() == "4" and not win.calc_panel.result_label.property("error")


def test_keyboard_does_not_leak_into_calculator_from_other_pages(win):
    win.btn_settings.click()
    keys(win, "123")
    assert win.calc_panel.display.text() == ""
    win.show_converter()
    QTest.keyClicks(win.converter.input, "5")
    assert win.calc_panel.display.text() == ""


# ---------------------------------------------------------------- окно
def test_rounded_corners_are_transparent(win):
    img = win.grab().toImage()
    assert img.pixelColor(0, 0).alpha() == 0 and img.pixelColor(img.width() - 1, 0).alpha() == 0
    assert img.pixelColor(img.width() // 2, img.height() // 2).alpha() > 200


def test_drag_by_free_area_but_not_by_widgets(win):
    win.move(100, 100)
    start = win.pos()
    lbl = win.calc_panel.result_label                   # QLabel — «свободная» область
    mouse(lbl, QEvent.MouseButtonPress, QPoint(300, 300))
    mouse(lbl, QEvent.MouseMove, QPoint(340, 330), Qt.NoButton)
    mouse(lbl, QEvent.MouseButtonRelease, QPoint(340, 330), Qt.LeftButton, Qt.NoButton)
    assert win.pos() - start == QPoint(40, 30)

    p1 = win.pos()
    btn = win.calc_panel.buttons["5"]                   # кнопка — окно не двигает
    mouse(btn, QEvent.MouseButtonPress, QPoint(300, 300))
    mouse(btn, QEvent.MouseMove, QPoint(380, 380), Qt.NoButton)
    mouse(btn, QEvent.MouseButtonRelease, QPoint(380, 380), Qt.LeftButton, Qt.NoButton)
    assert win.pos() == p1

    mb = win.menuBar()                                  # пустое место строки меню тоже тянет окно
    mouse(mb, QEvent.MouseButtonPress, QPoint(300, 300))
    mouse(mb, QEvent.MouseMove, QPoint(310, 320), Qt.NoButton)
    mouse(mb, QEvent.MouseButtonRelease, QPoint(310, 320), Qt.LeftButton, Qt.NoButton)
    assert win.pos() - p1 == QPoint(10, 20)


def test_minimize_and_close_buttons(win, qapp):
    box = win.menuBar().cornerWidget(Qt.TopRightCorner)
    minimize, close = box.findChildren(QPushButton)
    minimize.click(); qapp.processEvents()
    assert win.isMinimized()
    win.showNormal()
    close.click(); qapp.processEvents()
    assert not win.isVisible()


# ---------------------------------------------------------------- настройки: цвет, язык, тема, анимации
def test_accent_choice_recolors_everything_and_persists(win, qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor("#ff7a45")))
    win.btn_settings.click()
    before = win.grab().toImage()
    win.settings_panel.btn_color.click()
    assert win.theme.palette.accent.name() == "#ff7a45"
    assert win._fade.running                              # кросс-фейд пошёл
    assert wait_until(lambda: not win._fade.running, qapp)
    after = win.grab().toImage()
    assert before != after
    assert json.load(open(tmp_path / "config.json"))["accent"] == "#ff7a45"
    assert "#ff7a45" in qapp.styleSheet().lower()

    # после «перезапуска» цвет восстановлен
    s2 = Settings(str(tmp_path / "config.json"))
    w2 = MainWindow(s2, ThemeManager(s2, qapp), currency_service=FakeService())
    assert w2.theme.palette.accent.name() == "#ff7a45"
    w2.close()


def test_cancelled_color_dialog_changes_nothing(win, monkeypatch):
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor()))
    before = win.theme.palette
    win.settings_panel.pick_color()
    assert win.theme.palette == before and win.settings.get("accent") is None


def test_operator_and_accent_keys_follow_accent(win, qapp):
    def px(label):
        b = win.calc_panel.buttons[label]
        return b.grab().toImage().pixelColor(b.width() // 2, b.height() // 3).name()
    before = {l: px(l) for l in ("÷", "=", "7")}
    win.theme.set_accent("#00b3ff")
    wait_until(lambda: not win._fade.running, qapp)
    after = {l: px(l) for l in ("÷", "=", "7")}
    assert after["÷"] != before["÷"] and after["="] != before["="]


def test_theme_buttons_switch_theme_and_stay_in_sync(win, qapp):
    win.btn_settings.click()
    sp = win.settings_panel
    assert sp.btn_dark.isChecked() and not sp.btn_light.isChecked()
    sp.btn_light.click()
    assert win.theme.palette.theme == "light" and sp.btn_light.isChecked() and not sp.btn_dark.isChecked()
    sp.btn_light.click()                                  # повторный клик не «отщёлкивает» кнопку
    assert sp.btn_light.isChecked()
    assert wait_until(lambda: not win._fade.running, qapp)
    sp.btn_dark.click()
    assert win.theme.palette.theme == "dark"


def test_language_switch_updates_everything_and_persists(win, tmp_path):
    win.show_converter()
    win.btn_settings.click()
    win.settings_panel.lang_combo.setCurrentIndex(1)
    assert [b.text() for b in (win.btn_calc, win.btn_conv, win.btn_settings)] == ["Calculator", "Converter", "Settings"]
    assert not win.menuBar().actions()
    assert win.settings_panel.title_lbl.text() == "Settings" and win.settings_panel.anim_lbl.text() == "Animations"
    assert win.converter.title_lbl.text() == "Currency"
    assert json.load(open(tmp_path / "config.json"))["lang"] == "en"
    win.settings_panel.lang_combo.setCurrentIndex(0)
    assert win.btn_calc.text() == "Калькулятор"


def test_animations_switch_persists_and_disables_motion(win, qapp, tmp_path):
    win.btn_settings.click()
    sw = win.settings_panel.anim_switch
    assert sw.isChecked()
    sw.click()
    assert json.load(open(tmp_path / "config.json"))["animations"] is False
    win.btn_calc.click()
    assert not win.stack.animating                       # переход мгновенный
    win.theme.set_accent("#13ff8a")
    assert not win._fade.running                         # кросс-фейда нет
    assert win.theme.palette.accent.name() == "#13ff8a"  # но палитра применилась


def test_few_animation_objects_overall(win, qapp):
    win.btn_settings.click(); win.btn_calc.click(); win.show_converter()
    for b in win.findChildren(QPushButton):
        QApplication_send_enter(b)
    n = len(win.findChildren(QVariantAnimation))
    assert n <= len(win.findChildren(QPushButton)) + 12   # не «сотни»: по одной на взаимодействовавший виджет


def QApplication_send_enter(w):
    from PySide6.QtWidgets import QApplication
    QApplication.sendEvent(w, QEvent(QEvent.Enter))


# ---------------------------------------------------------------- устойчивость при запуске
def test_window_survives_corrupted_config(qapp, tmp_path):
    p = tmp_path / "config.json"
    p.write_text("\x00{{{ definitely not json", encoding="utf-8")
    s = Settings(str(p))
    w = MainWindow(s, ThemeManager(s, qapp), currency_service=FakeService())
    w.show()
    assert w.theme.palette.theme == "dark" and w.stack.currentWidget() is w.calc_panel
    w.close()


def test_real_entry_point_starts_and_builds_window():
    """python main.py: приложение запускается без ошибок (цикл событий подменён заглушкой)."""
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from PySide6.QtWidgets import QApplication\n"
        "seen = {}\n"
        "def fake_exec(self):\n"
        "    from app.ui.main_window import MainWindow\n"
        "    w = [x for x in QApplication.topLevelWidgets() if isinstance(x, MainWindow)][0]\n"
        "    seen['ok'] = w.isVisible() and w.stack.currentWidget() is w.calc_panel\n"
        "    return 0 if seen['ok'] else 3\n"
        "QApplication.exec = fake_exec\n"
        "import main\n"
        "sys.exit(main.main())\n"
    ) % ROOT
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
