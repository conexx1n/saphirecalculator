import os
import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.settings import Settings
from app.core.paths import data_dir
from app.styles.manager import ThemeManager
from app.ui.main_window import MainWindow


def _log_crash():
    try:
        path = str(data_dir() / "crash.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(traceback.format_exc() + "\n")
    except OSError:
        pass


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Sapphire Calculator")
    try:
        settings = Settings()
        theme = ThemeManager(settings, app)
        window = MainWindow(settings, theme)
        window.show()
    except Exception as e:               # ошибка запуска не должна заканчиваться «тихим» падением
        _log_crash()
        QMessageBox.critical(None, "Sapphire Calculator", f"Не удалось запустить приложение:\n{e}")
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
