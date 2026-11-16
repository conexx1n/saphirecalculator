from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from app.core.i18n import set_lang, t
from app.core.settings import Settings
from app.styles.manager import ThemeManager
from app.styles.tokens import RADIUS_WINDOW
from app.ui.background import render_background
from app.ui.calculator_panel import CalculatorPanel
from app.ui.controls import GlassButton
from app.ui.converter_panel import ConverterPanel
from app.ui.glass import palette_of
from app.ui.motion import CrossFade, FadeStack
from app.ui.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    """Каркас: безрамочное окно, навигация, стек страниц, фон, перетаскивание."""

    def __init__(self, settings: Settings, theme: ThemeManager = None, currency_service=None):
        super().__init__()
        self.settings = settings
        self.theme = theme or ThemeManager(settings)
        self._currency_service = currency_service
        set_lang(settings.get("lang", "ru"))

        self.setWindowTitle("Sapphire Calculator")
        self.setMinimumSize(480, 720)
        self.resize(480, 720)
        self.setMaximumWidth(600)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self._drag_pos = None
        self._bg_cache = None
        self._bg_key = None
        self.converter = None            # создаётся при первом открытии

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 14, 20, 20)
        layout.setSpacing(16)

        # Собственная верхняя панель вместо QMenuBar: перетаскивание работает
        # и на X11, и на Wayland, а системные кнопки остаются кликабельными
        self._title_bar = QWidget(root)
        self._title_bar.setObjectName("TitleBar")
        self._title_bar.setFixedHeight(38)
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(2, 0, 0, 0)
        title_layout.setSpacing(8)
        self._brand_label = QLabel("Sapphire Calculator")
        self._brand_label.setObjectName("BrandTitle")
        self._brand_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        title_layout.addWidget(self._brand_label)
        title_layout.addStretch(1)
        self.create_window_buttons(title_layout)
        self._title_bar.setMouseTracking(True)
        self._title_bar.installEventFilter(self)
        # Явный курсор показывает, что верхняя полоса является ручкой перемещения
        self._title_bar.setCursor(Qt.OpenHandCursor)
        layout.addWidget(self._title_bar)

        # --- навигация: Калькулятор / Конвертер / Настройки ---
        nav = QHBoxLayout()
        self.btn_calc = GlassButton("", "nav", self.theme)
        self.btn_conv = GlassButton("", "nav", self.theme)
        self.btn_settings = GlassButton("", "nav", self.theme)
        for b in (self.btn_calc, self.btn_conv, self.btn_settings):
            b.setCheckable(True)
            b.setFixedHeight(40)
            nav.addWidget(b)
        self.btn_calc.clicked.connect(lambda: self.set_mode(self.calc_panel))
        self.btn_conv.clicked.connect(self.show_converter)
        self.btn_settings.clicked.connect(lambda: self.set_mode(self.settings_panel))
        layout.addLayout(nav)

        # --- страницы ---
        self.stack = FadeStack(self.theme)
        self.calc_panel = CalculatorPanel(self.theme)
        self.settings_panel = SettingsPanel(self.theme, settings)
        self.settings_panel.language_changed.connect(self.change_language)
        self.settings_panel.gradient_changed.connect(self._on_gradient_changed)
        self.stack.addWidget(self.calc_panel)        # калькулятор — страница по умолчанию
        self.stack.addWidget(self.settings_panel)
        layout.addWidget(self.stack)
        layout.addStretch()

        self._retranslate_nav()
        self.set_mode(self.calc_panel)

        # --- плавная смена темы/акцента: снимок → новая палитра → растворение снимка ---
        self._fade = CrossFade(self, self.theme)
        self.theme.aboutToChange.connect(self._fade.capture)
        self.theme.changed.connect(self._on_palette_changed)

    # ------------------------------------------------------------ меню и кнопки окна
    def create_window_buttons(self, parent_layout):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        for sym, kind, slot in (("—", "ghost", self.showMinimized), ("✕", "danger_ghost", self.close)):
            b = GlassButton(sym, kind, self.theme)
            b.setFixedSize(30, 26)
            b.clicked.connect(slot)
            lay.addWidget(b)
        self._win_buttons = box
        parent_layout.addWidget(box)

    # ------------------------------------------------------------ страницы
    def open_converter(self, ctype, title):
        if self.converter is None:
            self.converter = ConverterPanel(ctype, title, self.theme, self._currency_service)
            self.stack.addWidget(self.converter)
        else:
            self.converter.set_type(ctype, title)
        self.set_mode(self.converter)

    def show_converter(self):
        if self.converter is None:
            self.open_converter("currency", "Валюта")
        else:
            self.set_mode(self.converter)

    def set_mode(self, page):
        self.stack.set_current(page)
        self.btn_calc.setChecked(page is self.calc_panel)
        self.btn_conv.setChecked(page is self.converter)
        self.btn_settings.setChecked(page is self.settings_panel)
        if page is self.converter:
            self.converter.on_activated()

    # ------------------------------------------------------------ язык
    def _retranslate_nav(self):
        self.btn_calc.setText(t("Калькулятор"))
        self.btn_conv.setText(t("Конвертер"))
        self.btn_settings.setText(t("Настройки"))

    def change_language(self, lang):
        set_lang(lang)
        self.settings.set("lang", lang)
        self.retranslate()

    def retranslate(self):
        self._retranslate_nav()
        self.settings_panel.retranslate()
        if self.converter is not None:
            self.converter.retranslate()

    # ------------------------------------------------------------ клавиатура
    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.calc_panel and self.calc_panel.handle_key(event):
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------ фон
    def _on_palette_changed(self):
        self._bg_cache = None
        self.update()
        self._fade.play()

    def _on_gradient_changed(self):
        self._bg_cache = None
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_fade"):
            self._fade.setGeometry(self.rect())

    def paintEvent(self, event):
        pal = palette_of(self.theme)
        direction = self.settings.get("gradient_direction", "diagonal")
        key = (self.size().width(), self.size().height(), pal.theme, pal.accent.rgb(), direction)
        if self._bg_cache is None or self._bg_key != key:     # размытие — один раз на размер/палитру/направление
            self._bg_cache = render_background(pal, self.width(), self.height(), direction=direction)
            self._bg_key = key
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), RADIUS_WINDOW, RADIUS_WINDOW)
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, self._bg_cache)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(pal.window_border, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), RADIUS_WINDOW, RADIUS_WINDOW)

    # ------------------------------------------------------------ перетаскивание окна
    def eventFilter(self, obj, event):
        if obj is self._title_bar:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._title_bar.setCursor(Qt.ClosedHandCursor)
                self._start_window_drag(event)
                return True
            if event.type() == QEvent.MouseMove and self._drag_pos is not None:
                delta = event.globalPosition().toPoint() - self._drag_pos
                self.move(self.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
                return True
            if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._drag_pos = None
                self._title_bar.setCursor(Qt.OpenHandCursor)
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._title_bar.geometry().contains(event.position().toPoint()):
            self._start_window_drag(event)
            return
        super().mousePressEvent(event)

    def _start_window_drag(self, event):
        """Запускает системное перемещение окна (важно для Wayland)."""
        if event.button() != Qt.LeftButton:
            return
        handle = self.windowHandle()
        if handle is not None and hasattr(handle, "startSystemMove"):
            try:
                if handle.startSystemMove():
                    event.accept()
                    return
            except (RuntimeError, TypeError):
                pass
        # Резервный вариант для оконных систем без startSystemMove
        self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
        super().mouseReleaseEvent(event)
