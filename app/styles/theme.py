"""Генерация QSS из палитры. Здесь нет ни одного «своего» цвета — только токены."""
from app.styles.palette import Palette, qss as c
from app.styles.tokens import FONT_ROUNDED, FONT_UI, RADIUS_CONTROL


def build_stylesheet(p: Palette) -> str:
    r = RADIUS_CONTROL
    return f"""
* {{ color: {c(p.text)}; font-family: {FONT_UI}; font-size: 14px; }}
QMainWindow {{ background: transparent; }}
QWidget#Root {{ background: transparent; }}
QToolTip {{ background: {c(p.menu_bg)}; color: {c(p.text)}; border: 1px solid {c(p.card_border)}; border-radius: 6px; padding: 4px 8px; }}

QMenuBar {{ background: transparent; color: {c(p.text)}; padding: 5px; }}
QMenuBar::item {{ padding: 6px 12px; background: transparent; border-radius: 8px; }}
QMenuBar::item:selected {{ background: {c(p.accent_soft)}; }}
QMenu {{ background: {c(p.menu_bg)}; color: {c(p.text)}; border: 1px solid {c(p.card_border)}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 22px; border-radius: 6px; background: transparent; }}
QMenu::item:selected {{ background: {c(p.accent_soft)}; }}
QDialog {{ background: {c(p.menu_bg)}; }}

QLabel {{ background: transparent; }}
QLabel#Title {{ font-size: 20px; font-weight: 700; }}
QLabel#BrandTitle {{ font-size: 15px; font-weight: 600; color: {c(p.text)}; }}
QLabel#SectionTitle {{ font-size: 16px; font-weight: 700; margin-top: 6px; }}
QLabel#Muted {{ color: {c(p.text_muted)}; }}
QLabel#BigResult {{ font-size: 34px; font-weight: 700; color: {c(p.accent_text)}; }}
QLabel#CalcResult {{ font-size: 38px; font-weight: 700; font-family: {FONT_ROUNDED}; }}
QLabel#CalcResult[error="true"] {{ color: {c(p.danger)}; }}
QLabel#Badge {{ background: {c(p.accent_soft)}; border-radius: 12px; font-weight: 700; font-size: 18px; }}
QLabel[tone="muted"] {{ color: {c(p.text_muted)}; font-size: 12px; }}
QLabel[tone="warning"] {{ color: {c(p.warning)}; font-size: 12px; }}
QLabel[tone="danger"] {{ color: {c(p.danger)}; font-size: 12px; }}
QLabel[tone="success"] {{ color: {c(p.success)}; font-size: 12px; }}
QLabel[level="danger"] {{ color: {c(p.danger)}; }}
QLabel[level="warning"] {{ color: {c(p.warning)}; }}
QLabel[level="success"] {{ color: {c(p.success)}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {c(p.field_bg)}; border: 1px solid {c(p.field_border)}; border-radius: {r}px; padding: 8px 10px;
    selection-background-color: {c(p.accent)}; selection-color: {c(p.text_on_accent)};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border: 1px solid {c(p.field_border_hover)}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {c(p.accent)}; }}
QLineEdit[invalid="true"] {{ border: 1px solid {c(p.danger)}; background: {c(p.danger_soft)}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {c(p.disabled_text)}; background: {c(p.disabled_bg)}; }}
QLineEdit#CalcDisplay {{ font-size: 16px; font-family: {FONT_ROUNDED}; border: none; background: transparent; padding: 2px; }}
QLineEdit#CalcDisplay:hover, QLineEdit#CalcDisplay:focus {{ border: none; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: {c(p.menu_bg)}; border: 1px solid {c(p.card_border)}; border-radius: 8px; padding: 4px; outline: none;
    selection-background-color: {c(p.accent_soft)}; selection-color: {c(p.text)};
}}

QPushButton {{ background: {c(p.field_bg)}; border: 1px solid {c(p.field_border)}; border-radius: {r}px; padding: 10px; }}
QPushButton:hover {{ background: {c(p.accent_soft)}; border: 1px solid {c(p.accent)}; }}
QPushButton:pressed {{ background: {c(p.accent_soft_hover)}; }}
QPushButton:checked {{ background: {c(p.accent_soft)}; border: 1px solid {c(p.accent)}; color: {c(p.accent_text)}; }}
QPushButton:disabled {{ color: {c(p.disabled_text)}; background: {c(p.disabled_bg)}; border: 1px solid {c(p.field_border)}; }}
QPushButton#Accent {{ background: {c(p.accent)}; color: {c(p.text_on_accent)}; border: none; font-weight: 600; }}
QPushButton#Accent:hover {{ background: {c(p.accent_hover)}; }}
QPushButton#Accent:pressed {{ background: {c(p.accent_pressed)}; }}
QWidget#Sidebar {{ background: {c(p.menu_bg)}; border-right: 1px solid {c(p.card_border)}; }}
QPushButton#NavButton {{ text-align: left; padding: 12px 16px; border: 1px solid transparent; background: transparent; }}
QPushButton#NavButton:hover {{ background: {c(p.hover_tint)}; }}
QPushButton#NavButton[active="true"] {{ background: {c(p.accent_soft)}; border: 1px solid {c(p.accent)}; color: {c(p.accent_text)}; font-weight: 600; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {c(p.field_border)}; border-radius: 5px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {c(p.accent)}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QListWidget, QTableWidget {{ background: {c(p.field_bg)}; border: 1px solid {c(p.field_border)}; border-radius: 12px; }}
QListWidget::item:selected, QTableWidget::item:selected {{ background: {c(p.accent_soft)}; color: {c(p.text)}; }}
QHeaderView::section {{ background: transparent; border: none; padding: 6px; color: {c(p.text_muted)}; }}
QProgressBar {{ background: {c(p.field_bg)}; border: 1px solid {c(p.field_border)}; border-radius: 8px; text-align: center; height: 22px; }}
QProgressBar::chunk {{ background: {c(p.accent)}; border-radius: 8px; }}
QStatusBar {{ background: {c(p.menu_bg)}; border-top: 1px solid {c(p.card_border)}; color: {c(p.text_muted)}; }}
"""


def apply_theme(app, settings):
    """Совместимый вход: строит палитру из настроек и применяет QSS."""
    palette = Palette.build(settings.get("theme", "dark"), settings.get("accent"))
    app.setStyleSheet(build_stylesheet(palette))
    return palette
