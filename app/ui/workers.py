import threading

from PySide6.QtCore import QObject, Signal


class RatesLoader(QObject):
    """Обновляет курсы валют в фоне, не блокируя GUI.

    Одновременно выполняется не более одного запроса. Поток daemon-ный, поэтому он не
    мешает закрытию приложения; результат доставляется в GUI-поток очередью сигналов.
    """

    finished = Signal(bool)     # True — курсы свежие
    _result = Signal(bool)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self._service = service
        self._busy = False
        self._result.connect(self._on_result)

    @property
    def busy(self):
        return self._busy

    def request(self, force=False):
        if self._busy:
            return False
        self._busy = True
        threading.Thread(target=self._run, args=(force,), daemon=True, name="rates-loader").start()
        return True

    def _run(self, force):
        try:
            ok = bool(self._service.fetch(force=force))
        except Exception:
            ok = False
        try:
            self._result.emit(ok)
        except RuntimeError:     # объект уже уничтожен вместе с окном
            pass

    def _on_result(self, ok):
        self._busy = False
        self.finished.emit(ok)
