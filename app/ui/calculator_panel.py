from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.core.calculator import evaluate, format_number
from app.core.i18n import t
from app.ui.controls import GlassButton
from app.ui.glass import GlassCard, repolish

KEYS = [
    ("%", "⌫", "C", "AC"),
    ("7", "8", "9", "÷"),
    ("4", "5", "6", "×"),
    ("1", "2", "3", "-"),
    ("0", ".", "=", "+"),
    ("(", ")", "√", "^"),
]
_OPERATORS = ("÷", "×", "-", "+")
_TYPED = "0123456789+-*/.(),%^"


class CalculatorPanel(QWidget):
    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.expression = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        display_card = GlassCard(theme=theme)
        dl = QVBoxLayout(display_card)
        dl.setContentsMargins(16, 16, 16, 16)
        self.display = QLineEdit()
        self.display.setObjectName("CalcDisplay")
        self.display.setReadOnly(True)
        self.display.setFocusPolicy(Qt.NoFocus)      # клавиатура всегда уходит в окно
        self.display.setAlignment(Qt.AlignRight)
        self.result_label = QLabel("0")
        self.result_label.setObjectName("CalcResult")
        self.result_label.setAlignment(Qt.AlignRight)
        dl.addWidget(self.display)
        dl.addWidget(self.result_label)
        layout.addWidget(display_card)

        grid_card = GlassCard(theme=theme)
        grid = QGridLayout(grid_card)
        grid.setSpacing(10)
        grid.setContentsMargins(16, 16, 16, 16)
        self.buttons = {}
        for r, row in enumerate(KEYS):
            for c, label in enumerate(row):
                kind = "operator" if label in _OPERATORS else "accent" if label == "=" else "key"
                btn = GlassButton(label, kind, theme)
                btn.setFixedHeight(60)
                btn.clicked.connect(lambda checked=False, l=label: self.press(l))
                grid.addWidget(btn, r, c)
                self.buttons[label] = btn
        layout.addWidget(grid_card)

    # --- логика ввода (поведение прежнее) ---------------------------------
    def _set_error(self, on):
        if bool(self.result_label.property("error")) != on:
            self.result_label.setProperty("error", on)
            repolish(self.result_label)

    def press(self, label):
        if label in ("AC", "C"):
            self.expression = ""
            self.display.setText("")
            self.result_label.setText("0")
            self._set_error(False)
        elif label == "⌫":
            self.expression = self.expression[:-1]
            self.display.setText(self.expression)
        elif label == "√":
            self.expression += "sqrt("
            self.display.setText(self.expression)
        elif label == "=":
            try:
                self.result_label.setText(format_number(evaluate(self.expression)))
                self._set_error(False)
            except Exception:
                self.result_label.setText(t("Ошибка"))
                self._set_error(True)
        else:
            self.expression += label.replace("÷", "/").replace("×", "*")
            self.display.setText(self.expression)

    def handle_key(self, event) -> bool:
        """Физическая клавиатура = нажатие соответствующих кнопок. True — клавиша обработана."""
        key, text = event.key(), event.text()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.press("=")
        elif key == Qt.Key_Backspace:
            self.press("⌫")
        elif key == Qt.Key_Escape:
            self.press("AC")
        elif text and text in _TYPED:
            self.press("." if text == "," else text)
        else:
            return False
        return True
