import time

from PySide6.QtCore import Qt, QRegularExpression, QSignalBlocker
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.core.currency import CurrencyService, ordered_codes
from app.core.i18n import decimal_sep, t
from app.core.units import (ConversionError, convert, convert_currency, format_money, format_value,
                            parse_number, unit_keys)
from app.ui.glass import GlassCard, repolish
from app.ui.controls import GlassButton
from app.ui.workers import RatesLoader

# Подписи единиц (русский текст — ключ перевода для app.core.i18n.t)
UNIT_LABELS = {
    "length": {"m": "Метры", "km": "Километры", "cm": "См", "mm": "Мм", "inch": "Дюймы"},
    "mass": {"kg": "Кг", "g": "Граммы", "mg": "Мг", "t": "Тонны"},
    "data": {"B": "Байты", "KB": "КБ", "MB": "МБ", "GB": "ГБ", "TB": "ТБ"},
    "speed": {"m/s": "М/с", "km/h": "Км/ч", "mph": "Мили/ч"},
    "time": {"s": "Секунды", "min": "Минуты", "h": "Часы", "d": "Дни"},
    "area": {"m2": "М²", "km2": "Км²", "cm2": "См²", "ha": "Гектары"},
    "volume": {"L": "Литры", "mL": "Мл", "m3": "М³", "gal": "Галлоны"},
    "temperature": {"C": "Цельсий", "F": "Фаренгейт", "K": "Кельвин"},
}
CONVERTERS = [
    ("Валюта", "currency"), ("Длина", "length"), ("Масса", "mass"),
    ("Данные", "data"), ("Температура", "temperature"), ("Скорость", "speed"),
    ("Объем", "volume"), ("Время", "time"), ("Площадь", "area"),
]

_HINTS = {"invalid": "Некорректное число", "range": "Слишком большое число",
          "abs_zero": "Ниже абсолютного нуля", "rate": "Нет курса для этой валюты"}
# Допустимые при наборе символы (в PCRE юникод-символы задаются как \x{...})
_INPUT_RE = QRegularExpression(r"[+\-\x{2212}]?[0-9 \x{a0}\x{202f}.,]*([eE][+\-]?[0-9]*)?")
assert _INPUT_RE.isValid()


class ConverterPanel(QWidget):
    """Конвертер без кнопки «Рассчитать»: результат пересчитывается при любом изменении
    значения, исходной или целевой единицы и при смене типа конвертера."""

    def __init__(self, ctype, title, theme=None, service=None, parent=None):
        super().__init__(parent)
        self.ctype, self.title_key = ctype, title
        self._svc, self._loader = service, None
        self._hint_code = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = GlassCard(theme=theme)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(12)

        # Категории расположены сеткой 3×3 — все видны одновременно, без прокрутки.
        self.category_grid = QGridLayout()
        self.category_grid.setContentsMargins(0, 0, 0, 0)
        self.category_grid.setHorizontalSpacing(8)
        self.category_grid.setVerticalSpacing(8)
        self.category_buttons = {}
        for index, (category_title, category_type) in enumerate(CONVERTERS):
            button = GlassButton(t(category_title), "nav", theme)
            button.setProperty("category_title", category_title)
            button.setCheckable(True)
            button.setFixedHeight(40)
            button.clicked.connect(
                lambda checked=False, c=category_type, title=category_title: self.set_type(c, title)
            )
            self.category_grid.addWidget(button, index // 3, index % 3)
            self.category_buttons[category_type] = button
        inner.addLayout(self.category_grid)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("Title")
        inner.addWidget(self.title_lbl)

        self.value_lbl = QLabel()
        self.value_lbl.setObjectName("Muted")
        inner.addWidget(self.value_lbl)
        self.input = QLineEdit("1")
        self.input.setMaxLength(64)
        self.input.setClearButtonEnabled(False)
        self.input.setValidator(QRegularExpressionValidator(_INPUT_RE, self.input))
        inner.addWidget(self.input)

        row = QHBoxLayout()
        self.from_combo, self.to_combo = QComboBox(), QComboBox()
        row.addWidget(self.from_combo, 1)
        row.addWidget(QLabel("➔"))
        row.addWidget(self.to_combo, 1)
        inner.addLayout(row)

        self.result = QLabel("—")
        self.result.setObjectName("BigResult")
        self.result.setAlignment(Qt.AlignCenter)
        self.result.setMinimumHeight(56)
        inner.addWidget(self.result)

        self.hint = QLabel()                       # ошибка ввода; фиксированная высота — без «прыжков» вёрстки
        self.hint.setProperty("tone", "danger")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setFixedHeight(18)
        self.status = QLabel()                     # состояние курсов (только для валют)
        self.status.setProperty("tone", "muted")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFixedHeight(18)
        inner.addWidget(self.hint)
        inner.addWidget(self.status)
        layout.addWidget(card)
        layout.addStretch(1)

        self.input.textChanged.connect(self.recalculate)
        self.from_combo.currentIndexChanged.connect(self.recalculate)
        self.to_combo.currentIndexChanged.connect(self.recalculate)
        self.set_type(ctype, title)

    # --- типы и единицы ---------------------------------------------------
    def set_type(self, ctype, title):
        self.ctype, self.title_key = ctype, title
        for category_type, button in self.category_buttons.items():
            selected = category_type == ctype
            blocker = QSignalBlocker(button)
            button.setChecked(selected)
            del blocker
            button.set_checked_visual(selected)
        self.title_lbl.setText(t(title))
        self.value_lbl.setText(t("Значение:"))
        if ctype == "currency":
            self._ensure_currency()
        for combo in (self.from_combo, self.to_combo):
            combo.blockSignals(True)
        self._populate()
        for combo in (self.from_combo, self.to_combo):
            combo.blockSignals(False)
        if ctype == "currency":
            self._kick_rates()
        self._refresh_status()
        self.recalculate()

    def _items(self):
        if self.ctype == "currency":
            return [(code, code) for code in ordered_codes(self._svc.rates)]
        labels = UNIT_LABELS.get(self.ctype, {})
        return [(t(labels.get(k, k)), k) for k in unit_keys(self.ctype)]

    def _populate(self, keep=None):
        for combo in (self.from_combo, self.to_combo):
            combo.clear()
            for text, key in self._items():
                combo.addItem(text, key)
        defaults = ("USD", "EUR") if self.ctype == "currency" else (None, None)
        for i, combo in enumerate((self.from_combo, self.to_combo)):
            wanted = keep[i] if keep else defaults[i]
            idx = combo.findData(wanted) if wanted else -1
            combo.setCurrentIndex(idx if idx >= 0 else min(i, combo.count() - 1))

    # --- расчёт -----------------------------------------------------------
    def recalculate(self, *_):
        try:
            value = parse_number(self.input.text())
            frm, to = self.from_combo.currentData(), self.to_combo.currentData()
            if frm is None or to is None:
                raise ConversionError("unit")
            if self.ctype == "currency":
                rates = self._svc.rates
                if frm not in rates or to not in rates:
                    raise ConversionError("rate")
                text = format_money(convert_currency(value, rates[frm], rates[to]), decimal_sep())
            else:
                text = format_value(convert(self.ctype, value, frm, to), decimal_sep())
        except ConversionError as e:
            self._show(None, e.code)
        else:
            self._show(text, None)

    def _show(self, text, code):
        out = text if text is not None else "—"     # при ошибке старый результат не остаётся
        if self.result.text() != out:
            self.result.setText(out)
        self._hint_code = code
        hint = t(_HINTS[code]) if code in _HINTS else ""
        if self.hint.text() != hint:
            self.hint.setText(hint)
        bad = code in ("invalid", "range", "abs_zero")
        if bool(self.input.property("invalid")) != bad:
            self.input.setProperty("invalid", bad)
            repolish(self.input)

    # --- валюты (сеть — в фоне) --------------------------------------------
    def _ensure_currency(self):
        if self._svc is None:
            self._svc = CurrencyService()
        if self._loader is None:
            self._loader = RatesLoader(self._svc, self)
            self._loader.finished.connect(self._on_rates)

    def _kick_rates(self):
        if not self._svc.is_fresh:                 # свежие курсы — сеть не трогаем
            self._loader.request()

    def _on_rates(self, ok):
        if self.ctype != "currency":
            return
        keep = (self.from_combo.currentData(), self.to_combo.currentData())
        if [c for _, c in self._items()] != [self.from_combo.itemData(i) for i in range(self.from_combo.count())]:
            for combo in (self.from_combo, self.to_combo):
                combo.blockSignals(True)
            self._populate(keep)
            for combo in (self.from_combo, self.to_combo):
                combo.blockSignals(False)
        self._refresh_status()
        self.recalculate()

    def _refresh_status(self):
        text, tone = "", "muted"
        if self.ctype == "currency":
            svc = self._svc
            stamp = time.strftime("%d.%m %H:%M", time.localtime(svc.updated_at)) if svc.updated_at else ""
            if self._loader is not None and self._loader.busy:
                text = t("Курсы обновляются…")
            elif svc.is_fresh:
                text, tone = f"{t('Курсы обновлены')} {stamp}", "success"
            elif svc.source == "cache":
                text, tone = f"{t('Офлайн: сохранённые курсы от')} {stamp}", "warning"
            else:
                text, tone = t("Нет сети: резервные курсы (могут быть неточными)"), "warning"
        if self.status.text() != text:
            self.status.setText(text)
        if self.status.property("tone") != tone:
            self.status.setProperty("tone", tone)
            repolish(self.status)

    # --- язык и активация ---------------------------------------------------
    def retranslate(self):
        self.title_lbl.setText(t(self.title_key))
        for category_type, button in self.category_buttons.items():
            button.setText(t(button.property("category_title")))
        self.value_lbl.setText(t("Значение:"))
        if self.ctype != "currency":
            labels = UNIT_LABELS.get(self.ctype, {})
            for combo in (self.from_combo, self.to_combo):
                for i in range(combo.count()):
                    combo.setItemText(i, t(labels.get(combo.itemData(i), combo.itemData(i))))
        self._refresh_status()
        self.recalculate()

    def on_activated(self):
        self.input.setFocus()
