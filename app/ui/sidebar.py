from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

NAV = [
    ("calculator", "Calculator"),
    ("currency", "Currency"),
    ("discount", "Discount"),
    ("pcpower", "PC Power"),
    ("probability", "Probability"),
    ("leveling", "Leveling"),
    ("history", "History"),
    ("settings", "Settings"),
]


class Sidebar(QWidget):
    navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self.buttons = {}
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 20, 16, 20)
        v.setSpacing(8)
        t = QLabel("Sapphire")
        t.setObjectName("Title")
        s = QLabel("Calculator")
        s.setObjectName("Muted")
        v.addWidget(t)
        v.addWidget(s)
        v.addSpacing(20)
        for key, label in NAV:
            b = QPushButton(label)
            b.setObjectName("NavButton")
            b.setProperty("active", "false")
            b.clicked.connect(lambda _=False, k=key: self._click(k))
            v.addWidget(b)
            self.buttons[key] = b
        v.addStretch(1)
        f = QLabel("v1.0 · conexx1n")
        f.setObjectName("Muted")
        f.setStyleSheet("font-size: 11px;")
        v.addWidget(f)

    def _click(self, k):
        self.set_active(k)
        self.navigate.emit(k)

    def set_active(self, k):
        for key, b in self.buttons.items():
            b.setProperty("active", "true" if key == k else "false")
            b.style().unpolish(b)
            b.style().polish(b)
