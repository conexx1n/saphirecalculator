from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class DiscountPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("Discount", "Sequential discounts"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)

        self.price = QDoubleSpinBox()
        self.price.setRange(0, 1e12)
        self.price.setValue(1000)
        self.price.setPrefix("$ ")
        self.discounts = QLineEdit("20, 10")
        self.discounts.setPlaceholderText("20, 10, 5")

        inner.addWidget(QLabel("Price before discount"))
        inner.addWidget(self.price)
        inner.addWidget(QLabel("Sequential discounts (%)"))
        inner.addWidget(self.discounts)

        b = QPushButton("Calculate")
        b.setObjectName("Accent")
        b.setMinimumHeight(44)
        b.clicked.connect(self._calc)
        inner.addWidget(b)

        self.final = QLabel("—")
        self.final.setObjectName("BigResult")
        self.saved = QLabel("")
        self.saved.setObjectName("Muted")
        inner.addWidget(self.final)
        inner.addWidget(self.saved)

        v.addWidget(card)
        v.addStretch(1)

    def _calc(self):
        try:
            price = self.price.value()
            cur = price
            for p in [x.strip() for x in self.discounts.text().split(",") if x.strip()]:
                pct = float(p)
                if not 0 <= pct <= 100:
                    raise ValueError("0..100")
                cur *= (1 - pct / 100)
            saved = price - cur
            self.final.setText(f"$ {cur:,.2f}")
            self.saved.setText(f"You save $ {saved:,.2f}")
            self.result_ready.emit("Discount", f"{price:.2f} - [{self.discounts.text()}]", f"{cur:.2f}")
        except Exception as e:
            self.final.setText("Error")
            self.saved.setText(str(e))
