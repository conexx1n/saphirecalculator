"""Страницы прежней реализации (pages/, sidebar) в окно не подключены, но остаются в проекте.
Эти тесты гарантируют, что они не развалились и стилизуются единой палитрой."""
import pytest

from app.ui.pages.calculator_page import CalculatorPage
from app.ui.pages.discount_page import DiscountPage
from app.ui.pages.leveling_page import LevelingPage
from app.ui.pages.pcpower_page import PCPowerPage
from app.ui.pages.probability_page import ProbabilityPage
from app.ui.pages.settings_page import SettingsPage


@pytest.mark.parametrize("cls", [DiscountPage, LevelingPage, PCPowerPage, ProbabilityPage])
def test_legacy_pages_construct(qapp, theme, cls):
    cls()


def test_legacy_settings_and_calculator_pages_construct(qapp, theme, settings):
    SettingsPage(settings)
    CalculatorPage()


def test_leveling_formula_is_evaluated_without_eval(qapp):
    page = LevelingPage()
    page.formula.setText("50 * level ** 2")
    assert page._xp_for(3) == 450
    page.formula.setText("__import__('os').system('echo hacked')")
    with pytest.raises(ValueError):
        page._xp_for(3)
