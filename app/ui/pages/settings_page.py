from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSlider,
    QSpinBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.styles.palette import DEFAULT_ACCENT
from app.ui.components.widgets import PageHeader
from app.ui.glass import GlassCard


class SocialCard(GlassCard):
    def __init__(self, name, desc, url, parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(18, 16, 18, 16)
        h.setSpacing(14)
        badge = QLabel(name[:1].upper())
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignCenter)
        badge.setObjectName("Badge")   # цвета — в app/styles/theme.py
        h.addWidget(badge)
        v = QVBoxLayout()
        n = QLabel(name)
        n.setStyleSheet("font-weight:600;")
        d = QLabel(desc)
        d.setObjectName("Muted")
        v.addWidget(n)
        v.addWidget(d)
        h.addLayout(v, 1)
        b = QPushButton("Open")
        b.setObjectName("Accent")
        b.setFixedWidth(90)
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        h.addWidget(b)


class SettingsPage(QWidget):
    settings_changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.s = settings
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)
        outer.addWidget(PageHeader("Settings", "Customize Sapphire Calculator"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        v = QVBoxLayout(cont)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(16)

        a = GlassCard()
        av = QVBoxLayout(a)
        av.setContentsMargins(24, 24, 24, 24)
        av.addWidget(QLabel("Appearance"))
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(self.s.get("theme", "dark"))
        self.theme.currentTextChanged.connect(lambda x: self._save("theme", x))
        av.addWidget(self._row("Theme", self.theme))

        self.accent = QLineEdit(self.s.get("accent") or DEFAULT_ACCENT["dark"])
        self.accent.editingFinished.connect(lambda: self._save("accent", self.accent.text()))
        av.addWidget(self._row("Accent color", self.accent))

        self.glass = QSlider(Qt.Horizontal)
        self.glass.setRange(0, 100)
        self.glass.setValue(int(self.s.get("glass_intensity", 60)))
        self.glass.valueChanged.connect(lambda x: self._save("glass_intensity", x))
        av.addWidget(self._row("Glass intensity", self.glass))

        self.anim = QCheckBox()
        self.anim.setChecked(bool(self.s.get("animations", True)))
        self.anim.toggled.connect(lambda x: self._save("animations", x))
        av.addWidget(self._row("Animations", self.anim))

        self.scale = QSpinBox()
        self.scale.setRange(75, 150)
        self.scale.setSuffix(" %")
        self.scale.setValue(int(self.s.get("scale", 100)))
        self.scale.valueChanged.connect(lambda x: self._save("scale", x))
        av.addWidget(self._row("UI scale", self.scale))
        v.addWidget(a)

        g = GlassCard()
        gv = QVBoxLayout(g)
        gv.setContentsMargins(24, 24, 24, 24)
        gv.addWidget(QLabel("General"))
        self.lang = QComboBox()
        self.lang.addItems(["en", "ru"])
        self.lang.setCurrentText(self.s.get("language", "en"))
        self.lang.currentTextChanged.connect(lambda x: self._save("language", x))
        gv.addWidget(self._row("Language", self.lang))

        self.autosave = QCheckBox()
        self.autosave.setChecked(bool(self.s.get("autosave", True)))
        self.autosave.toggled.connect(lambda x: self._save("autosave", x))
        gv.addWidget(self._row("Autosave history", self.autosave))

        self.notify = QCheckBox()
        self.notify.setChecked(bool(self.s.get("notifications", True)))
        self.notify.toggled.connect(lambda x: self._save("notifications", x))
        gv.addWidget(self._row("Notifications", self.notify))
        v.addWidget(g)

        ab = GlassCard()
        abv = QVBoxLayout(ab)
        abv.setContentsMargins(24, 24, 24, 24)
        abv.addWidget(QLabel("About"))
        abv.addWidget(QLabel("Sapphire Calculator · v1.0"))
        d = QLabel("Desktop calculator with a softly blurred gradient background and translucent cards. Built with PySide6 / Qt 6. Author: conexx1n.")
        d.setObjectName("Muted")
        d.setWordWrap(True)
        abv.addWidget(d)
        v.addWidget(ab)

        so = GlassCard()
        sov = QVBoxLayout(so)
        sov.setContentsMargins(24, 24, 24, 24)
        sov.addWidget(QLabel("Мои социальные сети"))
        soc = self.s.get("socials", {})
        sov.addWidget(SocialCard("GitHub", "Code and open source", soc.get("github", "https://github.com/yoshiruuuuuu1")))
        sov.addWidget(SocialCard("Telegram", "Contact and updates", soc.get("telegram", "https://t.me/y0shiru")))
        v.addWidget(so)

        v.addStretch(1)
        scroll.setWidget(cont)
        outer.addWidget(scroll, 1)

    def _row(self, label, widget):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        l = QLabel(label)
        l.setMinimumWidth(160)
        l.setObjectName("Muted")
        h.addWidget(l)
        h.addWidget(widget, 1)
        return w

    def _save(self, k, val):
        self.s.set(k, val)
        self.settings_changed.emit()
