# Словарь переводов. Ключ — русский текст (он же показывается в русском интерфейсе).
_LANG = "ru"

EN = {
    # режимы / меню
    "Калькулятор": "Calculator", "Конвертер": "Converter", "Настройки": "Settings", "Конвертация": "Conversion",
    "Валюта": "Currency", "Длина": "Length", "Масса": "Mass", "Данные": "Data", "Температура": "Temperature",
    "Скорость": "Speed", "Объем": "Volume", "Время": "Time", "Площадь": "Area",
    # конвертер
    "Значение:": "Value:", "Значение": "Value", "Рассчитать": "Calculate", "Ошибка": "Error", "Ошибка API": "API error",
    "Метры": "Meters", "Километры": "Kilometers", "См": "cm", "Мм": "mm", "Дюймы": "Inches",
    "Кг": "kg", "Граммы": "Grams", "Мг": "mg", "Тонны": "Tonnes",
    "Байты": "Bytes", "КБ": "KB", "МБ": "MB", "ГБ": "GB", "ТБ": "TB",
    "М/с": "m/s", "Км/ч": "km/h", "Мили/ч": "mph",
    "Секунды": "Seconds", "Минуты": "Minutes", "Часы": "Hours", "Дни": "Days",
    "М²": "m²", "Км²": "km²", "См²": "cm²", "Гектары": "Hectares",
    "Литры": "Liters", "Мл": "mL", "М³": "m³", "Галлоны": "Gallons",
    "Цельсий": "Celsius", "Фаренгейт": "Fahrenheit", "Кельвин": "Kelvin",
    # настройки
    "Тема": "Theme", "Тёмная": "Dark", "Светлая": "Light", "Цвет темы": "Theme color",
    "Выбрать цвет…": "Pick color…", "Выберите цвет темы": "Choose theme color",
    "Язык": "Language", "О программе": "About", "Автор": "Author",
    "Свернуть": "Minimize", "Закрыть": "Close",
    "Анимации": "Animations", "Внешний вид": "Appearance",
    # конвертер: статусы и подсказки
    "Курсы обновляются…": "Updating rates…", "Курсы обновлены": "Rates updated",
    "Офлайн: сохранённые курсы от": "Offline: saved rates from",
    "Нет сети: резервные курсы (могут быть неточными)": "No network: fallback rates (may be inaccurate)",
    "Некорректное число": "Invalid number", "Слишком большое число": "Number is too large",
    "Ниже абсолютного нуля": "Below absolute zero", "Нет курса для этой валюты": "No rate for this currency",
}

def set_lang(lang): global _LANG; _LANG = lang if lang in ("ru", "en") else "ru"
def get_lang(): return _LANG
def t(text): return EN.get(text, text) if _LANG == "en" else text
def decimal_sep(): return "," if _LANG == "ru" else "."
