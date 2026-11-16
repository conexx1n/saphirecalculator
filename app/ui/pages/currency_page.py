import time

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.currency import CurrencyService, NAMES
from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class CurrencyPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.svc = CurrencyService()
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("Currency", "Live rates + offline cache"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(12)

        row1 = QHBoxLayout()
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 1e12)
        self.amount.setDecimals(4)
        self.amount.setValue(1)
        self.from_cur = QComboBox()
        self.from_cur.addItems(sorted(NAMES))
        self.from_cur.setCurrentText("USD")
        row1.addWidget(QLabel("Amount"))
        row1.addWidget(self.amount, 2)
        row1.addWidget(self.from_cur, 1)
        sw = QPushButton("⇄")
        sw.setFixedWidth(50)
        sw.clicked.connect(self._swap)
        row1.addWidget(sw)
        inner.addLayout(row1)

        row2 = QHBoxLayout()
        self.to_cur = QComboBox()
        self.to_cur.addItems(sorted(NAMES))
        self.to_cur.setCurrentText("EUR")
        row2.addWidget(QLabel("Convert to"))
        row2.addStretch(1)
        row2.addWidget(self.to_cur, 1)
        inner.addLayout(row2)

        self.result = QLabel("—")
        self.result.setObjectName("BigResult")
        inner.addWidget(self.result)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        inner.addWidget(self.status)

        b = QPushButton("Convert")
        b.setObjectName("Accent")
        b.setMinimumHeight(44)
        b.clicked.connect(self._conv)
        inner.addWidget(b)
        rb = QPushButton("Refresh")
        rb.clicked.connect(self._refresh)
        inner.addWidget(rb)

        v.addWidget(card)
        v.addStretch(1)
        ok = self.svc.fetch()
        self._update_status(ok)

    def _update_status(self, ok):
        if self.svc.updated_at:
            t = time.strftime("%H:%M:%S", time.localtime(self.svc.updated_at))
            self.status.setText(f"Updated {t}" if ok else f"Offline — cached ({self.svc.error[:40]})")
        else:
            self.status.setText("No rate data")

    def _refresh(self):
        ok = self.svc.fetch(force=True)
        self._update_status(ok)
        self._conv()

    def _swap(self):
        a, b = self.from_cur.currentText(), self.to_cur.currentText()
        self.from_cur.setCurrentText(b)
        self.to_cur.setCurrentText(a)
        self._conv()

    def _conv(self):
        try:
            v = self.svc.convert(self.amount.value(), self.from_cur.currentText(), self.to_cur.currentText())
            txt = f"{v:,.4f} {self.to_cur.currentText()}"
            self.result.setText(txt)
            self.result_ready.emit(
                "Currency",
                f"{self.amount.value()} {self.from_cur.currentText()} -> {self.to_cur.currentText()}",
                txt,
            )
        except Exception as e:
            self.result.setText(f"Error: {e}")
