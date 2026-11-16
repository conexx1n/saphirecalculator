from fractions import Fraction as F

import pytest

from app.core.units import (CONVERTER_TYPES, UNITS, ConversionError, convert, convert_currency,
                            format_money, format_value, parse_number, unit_keys)


# ---------- ввод ----------
@pytest.mark.parametrize("text,expected", [
    ("1", F(1)), ("0", F(0)), ("-5", F(-5)), ("+7", F(7)),
    ("1.5", F(3, 2)), ("1,5", F(3, 2)), (".5", F(1, 2)), (",5", F(1, 2)), ("5.", F(5)),
    ("1 000", F(1000)), ("1 000,5", F(2001, 2)), ("1,234.5", F(2469, 2)), ("1.234,5", F(2469, 2)),
    ("1e3", F(1000)), ("1E-2", F(1, 100)), ("−3", F(-3)), ("  42  ", F(42)),
])
def test_parse_ok(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("text,code", [
    ("", "empty"), ("   ", "empty"),
    ("-", "incomplete"), ("+", "incomplete"), (".", "incomplete"), ("1e", "incomplete"), ("1e-", "incomplete"),
    ("abc", "invalid"), ("1.2.3", "invalid"), ("1,2,3", "invalid"), ("--1", "invalid"), ("1e1.5", "invalid"),
    ("1e999", "range"), ("1e-999", "range"), ("1" * 70, "range"),
])
def test_parse_errors(text, code):
    with pytest.raises(ConversionError) as e:
        parse_number(text)
    assert e.value.code == code


# ---------- форматирование ----------
@pytest.mark.parametrize("value,expected", [
    (F(1), "1"), (F(5), "5"), (F(10), "10"), (F(100), "100"), (F(0), "0"), (F(-3), "-3"),
    (F(1, 2), "0.5"), (F(5, 2), "2.5"), (F(-5, 2), "-2.5"),
    (F(1, 3), "0.333333333333"), (F(2, 3), "0.666666666667"),
    (F(1099511627776), "1099511627776"),          # точное целое не округляется
    (F(10) ** 16, "1e+16"), (F(10) ** 20, "1e+20"), (F(123456789, 1000) * 10 ** 15, "1.23456789e+20"),
    (F(1, 10**6), "0.000001"), (F(1, 10**7), "1e-7"), (F(1, 10**9), "1e-9"),
    (F(1234567, 100), "12345.67"),
])
def test_format_value(value, expected):
    assert format_value(value) == expected


def test_format_value_decimal_separator():
    assert format_value(F(5, 2), ",") == "2,5"
    assert format_value(F(10) ** 20 * 3 / 2, ",") == "1,5e+20"


@pytest.mark.parametrize("value,expected", [
    (F(92), "92"), (F(23, 25), "0.92"), (F(276345, 1000), "276.34"), (F(1, 2), "0.5"),
    (F(65, 10000), "0.0065"), (F(-23, 25), "-0.92"), (F(0), "0"), (F(1005, 1000), "1"),
])
def test_format_money(value, expected):
    assert format_money(value) == expected


# ---------- все типы конвертации ----------
KNOWN = [
    ("length", "1", "km", "m", "1000"), ("length", "3", "inch", "cm", "7.62"), ("length", "1", "m", "mm", "1000"),
    ("mass", "1", "t", "kg", "1000"), ("mass", "500", "g", "kg", "0.5"), ("mass", "1", "kg", "mg", "1000000"),
    ("data", "1", "KB", "B", "1024"), ("data", "1", "TB", "GB", "1024"), ("data", "1", "TB", "B", "1099511627776"),
    ("speed", "36", "km/h", "m/s", "10"), ("speed", "1", "mph", "m/s", "0.44704"),
    ("time", "1", "d", "h", "24"), ("time", "90", "min", "h", "1.5"), ("time", "1", "h", "s", "3600"),
    ("area", "1", "ha", "m2", "10000"), ("area", "1", "km2", "ha", "100"), ("area", "10000", "cm2", "m2", "1"),
    ("volume", "1", "m3", "L", "1000"), ("volume", "1", "gal", "L", "3.785411784"), ("volume", "250", "mL", "L", "0.25"),
    ("temperature", "0", "C", "F", "32"), ("temperature", "100", "C", "F", "212"), ("temperature", "32", "F", "C", "0"),
    ("temperature", "0", "C", "K", "273.15"), ("temperature", "273.15", "K", "C", "0"),
    ("temperature", "-40", "C", "F", "-40"), ("temperature", "300", "K", "F", "80.33"),
]


@pytest.mark.parametrize("ctype,value,frm,to,expected", KNOWN)
def test_convert_known(ctype, value, frm, to, expected):
    assert format_value(convert(ctype, parse_number(value), frm, to)) == expected


@pytest.mark.parametrize("ctype", [c for c in CONVERTER_TYPES if c != "currency"])
def test_every_unit_pair_roundtrips_and_identity(ctype):
    keys = unit_keys(ctype)
    assert len(keys) >= 3
    for a in keys:
        assert convert(ctype, F(7), a, a) == 7
        for b in keys:
            back = convert(ctype, convert(ctype, F(7, 3), a, b), b, a)
            assert back == F(7, 3)            # точная арифметика: без дрейфа float


def test_negative_values_allowed_except_below_absolute_zero():
    assert convert("length", F(-5), "km", "m") == -5000
    assert convert("temperature", F(-273), "C", "K") == F(15, 100)
    for args in ((F(-300), "C", "K"), (F(-500), "F", "C"), (F(-1), "K", "C")):
        with pytest.raises(ConversionError) as e:
            convert("temperature", *args)
        assert e.value.code == "abs_zero"


def test_unknown_unit_or_type():
    with pytest.raises(ConversionError):
        convert("length", F(1), "m", "parsec")
    with pytest.raises(ConversionError):
        convert("nonsense", F(1), "m", "km")
    with pytest.raises(ConversionError):
        convert("temperature", F(1), "C", "X")


def test_unit_tables_are_complete():
    for ctype, table in UNITS.items():
        assert all(f > 0 for f in table.values()), ctype


# ---------- валюты ----------
def test_currency_math():
    assert convert_currency(F(10), 1.0, 0.5) == 5
    assert format_money(convert_currency(F(100), 92.0, 1.0)) == "1.09"
    assert convert_currency(F(0), 1.0, 0.5) == 0


@pytest.mark.parametrize("rf,rt", [(0, 1), (1, 0), (-1, 1), ("x", 1), (None, 1)])
def test_currency_bad_rates(rf, rt):
    with pytest.raises(ConversionError) as e:
        convert_currency(F(1), rf, rt)
    assert e.value.code == "rate"
