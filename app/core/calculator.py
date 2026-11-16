import math

class MathError(Exception):
    pass

class SafeParser:
    def __init__(self, expr: str):
        self.expr = expr.replace(",", ".")
        self.tokens = self._tokenize(self.expr)
        self.pos = 0

    @staticmethod
    def _tokenize(expr):
        tokens, i, n = [], 0, len(expr)
        while i < n:
            c = expr[i]
            if c.isspace():
                i += 1; continue
            if c.isdigit() or c == '.':
                j = i
                while j < n and (expr[j].isdigit() or expr[j] == '.'):
                    j += 1
                try:
                    tokens.append(("num", float(expr[i:j])))
                except ValueError:
                    raise MathError(f"Bad number: {expr[i:j]}")
                i = j
            elif expr[i:i+4].lower() == "sqrt":
                tokens.append(("func", "sqrt")); i += 4
            elif c in "+-*/%^()":
                tokens.append(("op", c)); i += 1
            else:
                raise MathError(f"Unexpected character: {c}")
        return tokens

    def parse(self):
        r = self._expr()
        if self.pos != len(self.tokens):
            raise MathError("Unexpected token")
        return r

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)
    def _next(self):
        t = self._peek(); self.pos += 1; return t

    def _expr(self):
        v = self._term()
        while True:
            k, val = self._peek()
            if k == "op" and val in "+-":
                self._next(); r = self._term()
                v = v + r if val == "+" else v - r
            else:
                return v

    def _term(self):
        v = self._factor()
        while True:
            k, val = self._peek()
            if k == "op" and val in "*/%":
                self._next(); r = self._factor()
                if val == "*": v *= r
                elif val == "/":
                    if r == 0: raise MathError("Division by zero")
                    v /= r
                else:
                    if r == 0: raise MathError("Division by zero")
                    v %= r
            else:
                return v

    def _factor(self):
        k, val = self._peek()
        if k == "op" and val in "+-":
            self._next(); v = self._factor()
            return v if val == "+" else -v
        return self._power()

    def _power(self):
        b = self._primary()
        k, val = self._peek()
        if k == "op" and val == "^":
            self._next(); e = self._factor(); return _power(b, e)
        return b

    def _primary(self):
        k, val = self._next()
        if k == "num": return val
        if k == "func" and val == "sqrt":
            a = self._primary()
            if a < 0: raise MathError("Negative sqrt")
            return math.sqrt(a)
        if k == "op" and val == "(":
            inner = self._expr()
            kk, vv = self._next()
            if kk != "op" or vv != ")":
                raise MathError("Missing )")
            return inner
        raise MathError(f"Unexpected: {val}")

def _power(b, e):
    try:
        r = b ** e
    except ZeroDivisionError:
        raise MathError("Division by zero")
    except OverflowError:
        raise MathError("Overflow")
    if isinstance(r, complex):          # (-8)^0.5 в Python даёт complex
        raise MathError("Complex result")
    return r


def evaluate(expr: str) -> float:
    if not expr or not expr.strip():
        raise MathError("Empty")
    try:
        result = SafeParser(expr).parse()
    except RecursionError:
        raise MathError("Expression is too deep")
    if not math.isfinite(result):
        raise MathError("Overflow")
    return result

def format_number(n: float) -> str:
    if isinstance(n, float) and n.is_integer() and abs(n) < 1e15:
        return str(int(n))
    return f"{n:.10g}"