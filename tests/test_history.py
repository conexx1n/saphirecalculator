import os
import tempfile

from app.core.history import HistoryService


def test_crud():
    with tempfile.TemporaryDirectory() as d:
        s = HistoryService(os.path.join(d, "h.db"))
        s.add("Calculator", "1+1", "2")
        assert len(s.all()) == 1
        s.clear()
        assert len(s.all()) == 0
