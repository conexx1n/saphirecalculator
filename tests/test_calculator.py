import pytest

from app.core.calculator import MathError, evaluate, format_number


def test_basic():
    assert evaluate("1+1") == 2


def test_precedence():
    assert evaluate("10 - 3*2") == 4


def test_parens():
    assert evaluate("(10-3)*2") == 14


def test_power():
    assert evaluate("2^10") == 1024


def test_sqrt():
    assert abs(evaluate("sqrt(16)") - 4) < 1e-9


def test_div0():
    with pytest.raises(MathError):
        evaluate("10/0")


def test_format():
    assert format_number(10.0) == "10"


@pytest.mark.parametrize("expr", ["5%0", "0^-1", "1/(2-2)"])
def test_zero_division_variants_are_matherrors(expr):
    with pytest.raises(MathError):
        evaluate(expr)


@pytest.mark.parametrize("expr", ["1.2.3", ".", "1..2", "abc", "2+", "(1+2", "1+2)", "", "   ", "sqrt(-1)", "()"])
def test_malformed_input_is_mathrror_not_crash(expr):
    with pytest.raises(MathError):
        evaluate(expr)


@pytest.mark.parametrize("expr", ["(-8)^0.5", "10^1000", "9^9^9", "(" * 2000 + "1" + ")" * 2000])
def test_complex_overflow_and_deep_nesting(expr):
    with pytest.raises(MathError):
        evaluate(expr)


def test_negative_numbers_and_unary():
    assert evaluate("-2^2") == -4 and evaluate("2^-1") == 0.5 and evaluate("--3") == 3 and evaluate("3*-2") == -6
    assert evaluate("2^3^2") == 512 and evaluate("-7%3") == 2


def test_decimal_comma_and_float_noise():
    assert evaluate("1,5+1,5") == 3
    assert format_number(evaluate("0.1+0.2")) == "0.3"


def test_format_number_large_values_stay_short():
    assert format_number(1e20) == "1e+20" and format_number(123456789012345.0) == "123456789012345"
    assert format_number(-0.0) == "0" and format_number(2.5) == "2.5"
