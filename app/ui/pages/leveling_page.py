from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.core.calculator import MathError, evaluate
from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class LevelingPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("Leveling", "XP / level progression with custom formula"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)

        self.cl = QSpinBox()
        self.cl.setRange(1, 10000)
        self.cl.setValue(1)
        self.cxp = QSpinBox()
        self.cxp.setRange(0, 1_000_000_000)
        self.cxp.setValue(0)
        self.tl = QSpinBox()
        self.tl.setRange(2, 10000)
        self.tl.setValue(10)
        self.formula = QLineEdit("100 * level * level")

        inner.addWidget(QLabel("Current level"))
        inner.addWidget(self.cl)
        inner.addWidget(QLabel("Current XP"))
        inner.addWidget(self.cxp)
        inner.addWidget(QLabel("Target level"))
        inner.addWidget(self.tl)
        inner.addWidget(QLabel("XP formula (use 'level')"))
        inner.addWidget(self.formula)

        b = QPushButton("Calculate")
        b.setObjectName("Accent")
        b.setMinimumHeight(44)
        b.clicked.connect(self._calc)
        inner.addWidget(b)

        self.out = QLabel("—")
        self.out.setObjectName("BigResult")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        inner.addWidget(self.out)
        inner.addWidget(self.progress)

        v.addWidget(card)
        v.addStretch(1)

    def _xp_for(self, level):
        # Формула вычисляется безопасным парсером (без eval): 'level' подставляется числом, ** → ^
        expr = self.formula.text().strip() or "100 * level * level"
        try:
            return int(evaluate(expr.replace("**", "^").replace("level", f"({level})")))
        except (MathError, OverflowError, ValueError):
            raise ValueError("Invalid formula")

    def _calc(self):
        try:
            cl, cxp, tl = self.cl.value(), self.cxp.value(), self.tl.value()
            if tl <= cl:
                raise ValueError("Target level must be > current")
            total = sum(self._xp_for(l) for l in range(cl, tl))
            remaining = max(0, total - cxp)
            pct = min(100, int((cxp / total) * 100)) if total else 0
            self.out.setText(f"{remaining:,} XP to reach level {tl}")
            self.progress.setValue(pct)
            self.result_ready.emit("Leveling", f"L{cl}({cxp}XP)->L{tl}", f"{remaining} XP")
        except Exception as e:
            self.out.setText(f"Error: {e}")
            self.progress.setValue(0)
