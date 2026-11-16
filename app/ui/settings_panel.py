import webbrowser

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.i18n import t
from app.ui.controls import ColorSwatch, GlassButton, ToggleSwitch
from app.ui.glass import GlassCard

LINKS = (("Telegram  @bioimvtf", "https://t.me/bioimvtf"),
         ("GitHub  conexx1n", "https://github.com/conexx1n"))


class SettingsPanel(QWidget):
    """Страница настроек внутри главного окна. Тему и акцент меняет ThemeManager."""

    language_changed = Signal(str)
    gradient_changed = Signal()

    def __init__(self, theme, settings, parent=None):
        super().__init__(parent)
        self.theme, self.settings = theme, settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = GlassCard(theme=theme)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(10)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("Title")
        inner.addWidget(self.title_lbl)

        self.theme_lbl = QLabel()
        self.theme_lbl.setObjectName("Muted")
        inner.addWidget(self.theme_lbl)
        row = QHBoxLayout()
        self.btn_dark = GlassButton("", "nav", theme)
        self.btn_light = GlassButton("", "nav", theme)
        for b, name in ((self.btn_dark, "dark"), (self.btn_light, "light")):
            b.setCheckable(True)
            b.setFixedHeight(40)
            b.clicked.connect(lambda checked=False, n=name: self._set_theme(n))
            row.addWidget(b)
        inner.addLayout(row)

        self.color_lbl = QLabel()
        self.color_lbl.setObjectName("Muted")
        inner.addWidget(self.color_lbl)
        row = QHBoxLayout()
        self.swatch = ColorSwatch(theme)
        self.btn_color = GlassButton("", "default", theme)
        self.btn_color.setFixedHeight(40)
        self.btn_color.clicked.connect(self.pick_color)
        row.addWidget(self.swatch)
        row.addWidget(self.btn_color, 1)
        inner.addLayout(row)

        self.gradient_lbl = QLabel("Направление градиента")
        self.gradient_lbl.setObjectName("Muted")
        self.gradient_combo = QComboBox()
        self.gradient_options = [
            ("Диагональ ↘", "diagonal"),
            ("Диагональ ↙", "diagonal_reverse"),
            ("Горизонтально →", "horizontal"),
            ("Горизонтально ←", "horizontal_reverse"),
            ("Вертикально ↓", "vertical"),
            ("Вертикально ↑", "vertical_reverse"),
        ]
        for label, value in self.gradient_options:
            self.gradient_combo.addItem(label, value)
        current = settings.get("gradient_direction", "diagonal")
        idx = self.gradient_combo.findData(current)
        self.gradient_combo.setCurrentIndex(max(0, idx))
        self.gradient_combo.currentIndexChanged.connect(self._set_gradient)
        inner.addWidget(self.gradient_lbl)
        inner.addWidget(self.gradient_combo)

        self.lang_lbl = QLabel()
        self.lang_lbl.setObjectName("Muted")
        inner.addWidget(self.lang_lbl)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(0 if settings.get("lang", "ru") == "ru" else 1)
        self.lang_combo.currentIndexChanged.connect(lambda i: self.language_changed.emit(self.lang_combo.itemData(i)))
        inner.addWidget(self.lang_combo)

        row = QHBoxLayout()
        self.anim_lbl = QLabel()
        self.anim_switch = ToggleSwitch(theme)
        self.anim_switch.setChecked(bool(settings.get("animations", True)))
        self.anim_switch.toggled.connect(lambda v: settings.set("animations", bool(v)))
        row.addWidget(self.anim_lbl, 1)
        row.addWidget(self.anim_switch)
        inner.addLayout(row)

        self.about_lbl = QLabel()
        self.about_lbl.setObjectName("SectionTitle")
        inner.addWidget(self.about_lbl)
        row = QHBoxLayout()
        for text, url in LINKS:
            b = GlassButton(text, "default", theme)
            b.setFixedHeight(40)
            b.clicked.connect(lambda checked=False, u=url: webbrowser.open(u))
            row.addWidget(b)
        inner.addLayout(row)
        layout.addWidget(card)
        layout.addStretch(1)

        theme.changed.connect(self._sync_theme_buttons)
        self.retranslate()
        self._sync_theme_buttons()

    def _set_gradient(self, index):
        value = self.gradient_combo.itemData(index)
        if value:
            self.settings.set("gradient_direction", value)
            self.gradient_changed.emit()

    def _set_theme(self, name):
        self.theme.set_theme(name)
        self._sync_theme_buttons()          # кнопка текущей темы не должна «отщёлкиваться»

    def _sync_theme_buttons(self):
        current = self.settings.get("theme", "dark")
        self.btn_dark.setChecked(current == "dark")
        self.btn_light.setChecked(current == "light")

    def pick_color(self):
        c = QColorDialog.getColor(self.theme.palette.accent, self, t("Выберите цвет темы"))
        if c.isValid():
            self.theme.set_accent(c.name())

    def retranslate(self):
        self.title_lbl.setText(t("Настройки"))
        self.theme_lbl.setText(t("Тема"))
        self.btn_dark.setText(t("Тёмная"))
        self.btn_light.setText(t("Светлая"))
        self.color_lbl.setText(t("Цвет темы"))
        self.btn_color.setText(t("Выбрать цвет…"))
        self.lang_lbl.setText(t("Язык"))
        self.gradient_lbl.setText(t("Направление градиента"))
        self.anim_lbl.setText(t("Анимации"))
        self.about_lbl.setText(t("О программе") + " · " + t("Автор"))
