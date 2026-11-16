from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.core.calculator import MathError, evaluate, format_number
from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class CalculatorPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expression = ""
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("Calculator", "Safe math engine — + − × ÷ % ^ √ ( )"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(14)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setMinimumHeight(56)
        self.display.setStyleSheet("font-size: 22px; padding: 10px 14px;")
        inner.addWidget(self.display)

        self.preview = QLabel("")
        self.preview.setObjectName("Muted")
        self.preview.setAlignment(Qt.AlignRight)
        inner.addWidget(self.preview)

        self.result_label = QLabel("0")
        self.result_label.setObjectName("BigResult")
        self.result_label.setAlignment(Qt.AlignRight)
        inner.addWidget(self.result_label)

        grid = QGridLayout()
        grid.setSpacing(10)
        rows = [
            ("C", "sqrt", "(", ")", "/"),
            ("7", "8", "9", "^", "*"),
            ("4", "5", "6", "+", "-"),
            ("1", "2", "3", ".", "%"),
            ("0", "00", "⌫", "=", ""),
        ]
        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                if not label:
                    continue
                b = QPushButton(label)
                b.setMinimumHeight(48)
                b.setStyleSheet("font-size: 16px;")
                if label == "=":
                    b.setObjectName("Accent")
                b.clicked.connect(lambda _=False, l=label: self.on_button(l))
                grid.addWidget(b, r, c)
        inner.addLayout(grid)
        v.addWidget(card, 1)

    def on_button(self, label):
        if label == "C":
            self.expression = ""
            self.display.setText("")
            self.result_label.setText("0")
            self.preview.setText("")
            return
        if label == "⌫":
            self.expression = self.expression[:-1]
            self.display.setText(self.expression)
            return
        if label == "sqrt":
            self.expression += "sqrt("
            self.display.setText(self.expression)
            return
        if label == "=":
            self._eval()
            return
        self.expression += label
        self.display.setText(self.expression)
        try:
            if self.expression.strip():
                self.preview.setText("= " + format_number(evaluate(self.expression)))
        except MathError:
            self.preview.setText("")

    def _eval(self):
        try:
            r = evaluate(self.expression)
            f = format_number(r)
            self.result_label.setText(f)
            self.result_ready.emit("Calculator", self.expression, f)
        except MathError as e:
            self.result_label.setText(f"Error: {e}")
