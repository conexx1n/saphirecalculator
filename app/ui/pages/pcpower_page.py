from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class PCPowerPage(QWidget):
    result_ready = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("PC Power", "Wattage + PSU recommendation"))

        card = GlassCard()
        g = QGridLayout(card)
        g.setContentsMargins(24, 24, 24, 24)
        g.setHorizontalSpacing(20)
        g.setVerticalSpacing(10)

        def row(r, label, mn, mx, val):
            sp = QSpinBox()
            sp.setRange(mn, mx)
            sp.setValue(val)
            sp.setSuffix(" W")
            g.addWidget(QLabel(label), r, 0)
            g.addWidget(sp, r, 1)
            return sp

        self.cpu = row(0, "CPU (TDP)", 5, 500, 65)
        self.gpu = row(1, "GPU (TDP)", 5, 900, 200)
        self.ram = row(2, "RAM", 4, 300, 32)
        self.storage = row(3, "SSD/HDD", 0, 200, 15)
        self.fans = row(4, "Fans", 0, 100, 10)
        self.mobo = row(5, "Motherboard", 5, 150, 30)
        self.extra = row(6, "Extra devices", 0, 200, 10)

        self.result = QLabel("—")
        self.result.setObjectName("BigResult")
        g.addWidget(self.result, 7, 0, 1, 2)
        self.warn = QLabel("")
        self.warn.setWordWrap(True)
        g.addWidget(self.warn, 8, 0, 1, 2)

        b = QPushButton("Calculate")
        b.setObjectName("Accent")
        b.setMinimumHeight(44)
        b.clicked.connect(self._calc)
        g.addWidget(b, 9, 0, 1, 2)
        v.addWidget(card)
        v.addStretch(1)

    def _calc(self):
        total = (
            self.cpu.value() + self.gpu.value() + self.ram.value()
            + self.storage.value() + self.fans.value() + self.mobo.value() + self.extra.value()
        )
        psu = int((total * 1.5) / 50) * 50 + 50
        self.result.setText(f"Load ≈ {total} W · PSU ≥ {psu} W")
        if total > 850:
            self.warn.setText("⚠ Very high load.")
            self.warn.setProperty("level", "danger")
        elif total > 550:
            self.warn.setText("Consider 80+ Gold.")
            self.warn.setProperty("level", "warning")
        else:
            self.warn.setText("Headroom OK.")
            self.warn.setProperty("level", "success")
        self.warn.style().unpolish(self.warn)
        self.warn.style().polish(self.warn)
        self.result_ready.emit(
            "PC Power",
            f"CPU{self.cpu.value()} GPU{self.gpu.value()} RAM{self.ram.value()}",
            f"{total}W / PSU {psu}W",
        )
