import time

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class HistoryPage(QWidget):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.h = history
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        v.addWidget(PageHeader("History", "All recorded calculations"))

        card = GlassCard()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(12)

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        self.search.textChanged.connect(self.refresh)
        self.filter = QComboBox()
        self.filter.addItem("All", "")
        for t in ["Calculator", "Currency", "Discount", "PC Power", "Probability", "Leveling"]:
            self.filter.addItem(t, t)
        self.filter.currentIndexChanged.connect(self.refresh)
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear)
        top.addWidget(self.search, 1)
        top.addWidget(self.filter)
        top.addWidget(clear)
        inner.addLayout(top)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Type", "Input", "Result", "When", "id"])
        self.table.setColumnHidden(4, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        inner.addWidget(self.table, 1)

        row = QHBoxLayout()
        c = QPushButton("Copy result")
        c.clicked.connect(self._copy)
        d = QPushButton("Delete")
        d.clicked.connect(self._delete)
        row.addWidget(c)
        row.addWidget(d)
        inner.addLayout(row)
        v.addWidget(card, 1)
        self.refresh()

    def refresh(self):
        rows = self.h.all(self.search.text(), self.filter.currentData() or "")
        self.table.setRowCount(len(rows))
        for i, (eid, ct, inp, res, ts) in enumerate(rows):
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
            for col, txt in enumerate([ct, inp, res, when, str(eid)]):
                self.table.setItem(i, col, QTableWidgetItem(txt))

    def _clear(self):
        if QMessageBox.question(self, "Clear", "Delete all history?") == QMessageBox.Yes:
            self.h.clear()
            self.refresh()

    def _copy(self):
        r = self.table.currentRow()
        if r >= 0:
            QGuiApplication.clipboard().setText(self.table.item(r, 2).text())

    def _delete(self):
        r = self.table.currentRow()
        if r >= 0:
            self.h.delete(int(self.table.item(r, 4).text()))
            self.refresh()
