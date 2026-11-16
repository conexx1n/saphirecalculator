import math

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class ProbabilityPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("Probability", "At-least-one + binomial"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)

        self.chance = QDoubleSpinBox()
        self.chance.setRange(0, 100)
        self.chance.setValue(5)
        self.chance.setSuffix(" %")
        self.tries = QSpinBox()
        self.tries.setRange(1, 1_000_000)
        self.tries.setValue(20)
        self.k = QSpinBox()
        self.k.setRange(0, 1_000_000)
        self.k.setValue(1)

        inner.addWidget(QLabel("Chance per attempt"))
        inner.addWidget(self.chance)
        inner.addWidget(QLabel("Attempts"))
        inner.addWidget(self.tries)
        inner.addWidget(QLabel("Wanted successes"))
        inner.addWidget(self.k)

        b = QPushButton("Calculate")
        b.setObjectName("Accent")
        b.setMinimumHeight(44)
        b.clicked.connect(self._calc)
        inner.addWidget(b)

        self.out1 = QLabel("—")
        self.out1.setObjectName("BigResult")
        self.out2 = QLabel("")
        self.out2.setObjectName("Muted")
        inner.addWidget(self.out1)
        inner.addWidget(self.out2)

        v.addWidget(card)
        v.addStretch(1)

    def _calc(self):
        p = self.chance.value() / 100.0
        n = self.tries.value()
        k = self.k.value()
        at_least = 0.0 if p <= 0 else 1 - (1 - p) ** n
        binom = 0.0 if k > n else math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
        self.out1.setText(f"At least one: {at_least * 100:.4f}%")
        self.out2.setText(f"Exactly {k}/{n}: {binom * 100:.4f}%")
        self.result_ready.emit("Probability", f"p={p * 100}% n={n} k={k}", f"{at_least * 100:.4f}%")
