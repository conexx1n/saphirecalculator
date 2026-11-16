"""Чистая логика конвертера (без Qt): парсинг ввода, пересчёт единиц, форматирование.

Все вычисления идут на fractions.Fraction, поэтому нет артефактов float
(0.1 + 0.2, 3 дюйма → 7.619999…) и точность теряется только при финальном округлении.
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction

F = Fraction

# Коэффициенты «единица → базовая единица типа».
UNITS: dict[str, dict[str, Fraction]] = {
    "length": {"m": F(1), "km": F(1000), "cm": F(1, 100), "mm": F(1, 1000), "inch": F(254, 10000)},
    "mass": {"kg": F(1), "g": F(1, 1000), "mg": F(1, 10**6), "t": F(1000)},
    "data": {"B": F(1), "KB": F(1024), "MB": F(1024**2), "GB": F(1024**3), "TB": F(1024**4)},
    "speed": {"m/s": F(1), "km/h": F(10, 36), "mph": F(44704, 100000)},
    "time": {"s": F(1), "min": F(60), "h": F(3600), "d": F(86400)},
    "area": {"m2": F(1), "km2": F(10**6), "cm2": F(1, 10**4), "ha": F(10**4)},
    # US gallon = 3.785411784 л (точное определение)
    "volume": {"L": F(1), "mL": F(1, 1000), "m3": F(1000), "gal": F(3785411784, 10**9)},
}
TEMPERATURE_UNITS = ("C", "F", "K")
CONVERTER_TYPES = ("currency", "length", "mass", "data", "temperature", "speed", "volume", "time", "area")

_K0 = F(27315, 100)  # 0 °C в кельвинах

MAX_ABS_EXPONENT = 300
MAX_DIGITS = 60
SIG_DIGITS = 12          # значащих цифр для неточных результатов
EXACT_DIGITS = 15        # точные результаты показываем целиком до 15 цифр
SCI_UPPER = 16           # от 1e16 — научная нотация
SCI_LOWER = -6           # меньше 1e-6 — научная нотация


class ConversionError(ValueError):
    """code: empty | incomplete | invalid | range | abs_zero | unit | rate"""

    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


def unit_keys(ctype: str) -> list[str]:
    if ctype == "temperature":
        return list(TEMPERATURE_UNITS)
    return list(UNITS.get(ctype, {}))


# ---------------------------------------------------------------- ввод
_NUM = re.compile(r"^[+-]?(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?$")
_INCOMPLETE = re.compile(r"^[+-]?([.,]|(\d+[.,]?\d*|[.,]\d+)[eE][+-]?)?$")


def parse_number(text: str) -> Fraction:
    """'1,5', '1.5', '1 000,5', '1,234.5', '1e3' → Fraction. Бросает ConversionError."""
    s = (text or "").strip()
    for ch in ("\u00a0", "\u202f", " "):
        s = s.replace(ch, "")
    s = s.replace("\u2212", "-")
    if not s:
        raise ConversionError("empty")
    if "," in s and "." in s:  # последний разделитель — десятичный, остальные — группировка
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        grp = "." if dec == "," else ","
        s = s.replace(grp, "").replace(dec, ".")
    else:
        s = s.replace(",", ".")
    if not _NUM.match(s):
        if _INCOMPLETE.match(s):
            raise ConversionError("incomplete")
        raise ConversionError("invalid")
    d = Decimal(s)
    if d != 0 and (abs(d.adjusted()) > MAX_ABS_EXPONENT or len(d.as_tuple().digits) > MAX_DIGITS):
        raise ConversionError("range")
    return Fraction(d)


# ---------------------------------------------------------------- расчёт
def _to_kelvin(v: Fraction, unit: str) -> Fraction:
    if unit == "K":
        return v
    if unit == "C":
        return v + _K0
    return (v - 32) * F(5, 9) + _K0  # F


def _from_kelvin(k: Fraction, unit: str) -> Fraction:
    if unit == "K":
        return k
    if unit == "C":
        return k - _K0
    return (k - _K0) * F(9, 5) + 32  # F


def convert(ctype: str, value: Fraction, frm: str, to: str) -> Fraction:
    if ctype == "temperature":
        if frm not in TEMPERATURE_UNITS or to not in TEMPERATURE_UNITS:
            raise ConversionError("unit")
        kelvin = _to_kelvin(value, frm)
        if kelvin < 0:
            raise ConversionError("abs_zero")
        return _from_kelvin(kelvin, to)
    table = UNITS.get(ctype)
    if table is None or frm not in table or to not in table:
        raise ConversionError("unit")
    return value * table[frm] / table[to]


def convert_currency(value: Fraction, rate_from, rate_to) -> Fraction:
    """Курсы заданы относительно USD: value / rate_from * rate_to."""
    try:
        rf, rt = Fraction(str(rate_from)), Fraction(str(rate_to))
    except (ValueError, ZeroDivisionError):
        raise ConversionError("rate")
    if rf <= 0 or rt <= 0:
        raise ConversionError("rate")
    return value / rf * rt


# ---------------------------------------------------------------- вывод
def _round_sig(x: Fraction, prec: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = prec
        ctx.rounding = ROUND_HALF_EVEN
        ctx.Emax = 10**6
        ctx.Emin = -10**6
        return Decimal(x.numerator) / Decimal(x.denominator)


def _decimal_to_text(d: Decimal, decimal: str) -> str:
    adj = d.adjusted()
    if adj >= SCI_UPPER or adj < SCI_LOWER:
        text = format(d.normalize(), "e")
    else:
        text = format(d, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
    return text.replace(".", decimal)


def format_value(x: Fraction, decimal: str = ".") -> str:
    """Без незначащих нулей; точные результаты (до 15 цифр) показываются полностью."""
    if x == 0:
        return "0"
    neg, a = x < 0, abs(x)
    d12, d15 = _round_sig(a, SIG_DIGITS), _round_sig(a, EXACT_DIGITS)
    d = d12 if (Fraction(d12) == a or Fraction(d15) != a) else d15
    return ("-" if neg else "") + _decimal_to_text(d, decimal)


def format_money(x: Fraction, decimal: str = ".") -> str:
    """Денежные суммы: 2 знака после запятой, мелкие значения — 4 значащие цифры."""
    if x == 0:
        return "0"
    neg, a = x < 0, abs(x)
    if a >= F(1, 100):
        if a >= 10**SCI_UPPER:
            return format_value(x, decimal)
        cents = (a * 100)
        d = (Decimal(cents.numerator) / Decimal(cents.denominator)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN) / 100
        text = format(d, "f")
        text = text.rstrip("0").rstrip(".") if "." in text else text
        text = text.replace(".", decimal)
    else:
        text = _decimal_to_text(_round_sig(a, 4), decimal)
    return ("-" if neg else "") + text
