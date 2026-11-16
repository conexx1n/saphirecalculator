"""Совместимость: прежнее имя ConverterDialog (раньше — отдельное окно) теперь встраиваемая панель."""
from app.ui.converter_panel import ConverterPanel


class ConverterDialog(ConverterPanel):
    def __init__(self, ctype, title, parent=None, **kwargs):
        super().__init__(ctype, title, parent=parent, **kwargs)
