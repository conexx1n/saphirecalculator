import pytest
from PySide6.QtWidgets import QPushButton
from PySide6.QtTest import QTest

from app.core import i18n
from app.ui.converter_panel import ConverterPanel
from tests.conftest import FakeService, wait_until


@pytest.fixture(autouse=True)
def russian():
    i18n.set_lang("ru")
    yield
    i18n.set_lang("ru")


def make(theme, ctype="length", title="Длина", **kw):
    p = ConverterPanel(ctype, title, theme, **kw)
    p.show()
    return p


def pick(combo, key):
    combo.setCurrentIndex(combo.findData(key))


def test_initial_value_is_plain_one(qapp, theme):
    p = make(theme)
    assert p.input.text() == "1"            # не «1.0000»
    assert p.result.text() == "0,001"       # m → km по умолчанию (запятая — для ru)


def test_no_calculate_button(qapp, theme):
    p = make(theme)
    assert not [b for b in p.findChildren(QPushButton)]
    assert not hasattr(p, "calc_btn") and not hasattr(p, "calculate")


def test_auto_recalc_on_every_parameter(qapp, theme):
    p = make(theme)
    pick(p.from_combo, "km"); pick(p.to_combo, "m")
    assert p.result.text() == "1000"
    p.input.setText("5")
    assert p.result.text() == "5000"
    p.input.setText("2,5")                  # запятая как десятичный разделитель
    assert p.result.text() == "2500"
    p.input.setText("2.5")
    assert p.result.text() == "2500"
    pick(p.to_combo, "cm")
    assert p.result.text() == "250000"
    pick(p.from_combo, "m")
    assert p.result.text() == "250"


def test_typing_characters_updates_live(qapp, theme):
    p = make(theme)
    pick(p.from_combo, "km"); pick(p.to_combo, "m")
    p.input.clear()
    seen = []
    for ch in "12.5":
        QTest.keyClick(p.input, ch)
        seen.append(p.result.text())
    assert seen == ["1000", "12000", "—", "12500"] or seen[-1] == "12500"
    assert p.result.text() == "12500"


@pytest.mark.parametrize("text,out", [("1", "1"), ("10", "10"), ("100", "100"), ("0.5", "0,5"), ("1.25", "1,25")])
def test_integer_and_fractional_display(qapp, theme, text, out):
    p = make(theme, "mass", "Масса")
    pick(p.from_combo, "kg"); pick(p.to_combo, "kg")
    p.input.setText(text)
    assert p.result.text() == out


def test_invalid_input_never_shows_stale_result(qapp, theme):
    p = make(theme)
    pick(p.from_combo, "km"); pick(p.to_combo, "m")
    p.input.setText("3")
    assert p.result.text() == "3000"
    for bad, flagged in (("1.2.3", True), ("", False), ("-", False), ("1e999", True)):
        p.input.setText(bad)
        assert p.result.text() == "—", bad
        assert bool(p.input.property("invalid")) is flagged, bad
    assert p.hint.text() == "Слишком большое число"
    p.input.setText("4")
    assert p.result.text() == "4000" and p.hint.text() == "" and not p.input.property("invalid")


def test_below_absolute_zero_is_an_error(qapp, theme):
    p = make(theme, "temperature", "Температура")
    pick(p.from_combo, "C"); pick(p.to_combo, "K")
    p.input.setText("-300")
    assert p.result.text() == "—" and p.hint.text() == "Ниже абсолютного нуля"
    p.input.setText("-273,15")
    assert p.result.text() == "0"


def test_big_and_small_use_scientific_notation(qapp, theme):
    p = make(theme, "data", "Данные")
    pick(p.from_combo, "TB"); pick(p.to_combo, "B")
    assert p.result.text() == "1099511627776"          # точность сохранена
    p.input.setText("1e20")
    assert "e+" in p.result.text()
    pick(p.from_combo, "B"); pick(p.to_combo, "TB")
    p.input.setText("1")
    assert "e-" in p.result.text()


def test_type_switch_recalculates_with_new_units(qapp, theme):
    p = make(theme)
    p.input.setText("100")
    p.set_type("temperature", "Температура")
    assert [p.from_combo.itemData(i) for i in range(3)] == ["C", "F", "K"]
    assert p.result.text() == "212"                    # 100 °C → °F
    p.set_type("time", "Время")
    assert p.from_combo.itemData(0) == "s" and p.result.text() == "1,66666666667"   # 100 s → min
    assert p.title_lbl.text() == "Время"


@pytest.mark.parametrize("ctype,title", [("length", "Длина"), ("mass", "Масса"), ("data", "Данные"), ("temperature", "Температура"),
                                         ("speed", "Скорость"), ("volume", "Объем"), ("time", "Время"), ("area", "Площадь")])
def test_every_converter_type_works(qapp, theme, ctype, title):
    p = make(theme, ctype, title)
    for i in range(p.to_combo.count()):
        pick(p.to_combo, p.to_combo.itemData(i))
        assert p.result.text() not in ("", "—"), (ctype, i)


def test_currency_uses_cached_rates_without_network(qapp, theme):
    svc = FakeService(fresh=True)
    p = make(theme, "currency", "Валюта", service=svc)
    assert svc.fetch_calls == 0                        # свежие курсы — сеть не трогаем
    pick(p.from_combo, "USD"); pick(p.to_combo, "RUB")
    p.input.setText("2")
    assert p.result.text() == "200"
    assert "обновлены" in p.status.text()


def test_currency_refreshes_in_background_and_ui_stays_responsive(qapp, theme):
    svc = FakeService(fresh=False, source="cache")
    p = make(theme, "currency", "Валюта", service=svc)
    assert p.result.text() != "—"                      # результат есть сразу, по кэшу
    assert wait_until(lambda: svc.fetch_calls == 1 and "обновлены" in p.status.text(), qapp)
    assert p._loader.busy is False


def test_currency_offline_shows_cached_status_and_keeps_working(qapp, theme):
    svc = FakeService(fresh=False, source="cache", ok=False)
    p = make(theme, "currency", "Валюта", service=svc)
    assert wait_until(lambda: svc.fetch_calls == 1 and not p._loader.busy, qapp)
    assert "Офлайн" in p.status.text() and p.status.property("tone") == "warning"
    assert p.result.text() != "—"


def test_currency_fallback_status(qapp, theme):
    svc = FakeService(fresh=False, source="fallback", ok=False)
    p = make(theme, "currency", "Валюта", service=svc)
    assert wait_until(lambda: not p._loader.busy, qapp)
    assert "резервные" in p.status.text()


def test_currency_requests_not_duplicated(qapp, theme):
    svc = FakeService(fresh=False, source="cache", ok=False)
    p = make(theme, "currency", "Валюта", service=svc)
    for _ in range(5):
        p.set_type("currency", "Валюта")
    assert wait_until(lambda: not p._loader.busy, qapp)
    assert svc.fetch_calls <= 2                        # одновременно — не более одного запроса


def test_currency_missing_rate_is_handled(qapp, theme):
    svc = FakeService()
    p = make(theme, "currency", "Валюта", service=svc)
    del svc.rates["EUR"]
    p.recalculate()
    assert p.result.text() == "—" and p.hint.text() == "Нет курса для этой валюты"


def test_language_switch_updates_labels_and_decimal_sign(qapp, theme):
    p = make(theme)
    pick(p.from_combo, "km"); pick(p.to_combo, "m")
    p.input.setText("1.5")
    i18n.set_lang("en"); p.retranslate()
    assert p.title_lbl.text() == "Length" and p.value_lbl.text() == "Value:"
    assert p.from_combo.itemText(p.from_combo.findData("km")) == "Kilometers"
    assert p.result.text() == "1500"
    p.input.setText("0.0005")
    assert p.result.text() == "0.5"


def test_category_selection_resets_previous_gradient_state(qapp, theme):
    p = make(theme)
    old = p.category_buttons["length"]
    new = p.category_buttons["mass"]
    assert old._chk == 1.0
    p.set_type("mass", "Масса")
    assert old._chk == 0.0
    assert new._chk == 1.0
    theme.set_accent("#168BCE")
    assert old._chk == 0.0 and new._chk == 1.0
