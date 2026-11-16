import json
import os

from app.core.settings import DEFAULTS, Settings


def test_persist():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.json")
        Settings(p).set("theme", "light")
        assert Settings(p).get("theme") == "light"


def test_defaults(tmp_path):
    s = Settings(str(tmp_path / "c.json"))
    assert s.data == DEFAULTS and s.get("animations") is True and s.get("accent") is None


def test_accent_and_language_survive_restart(tmp_path):
    p = str(tmp_path / "c.json")
    s = Settings(p)
    s.set("accent", "#ff7a45"); s.set("lang", "en"); s.set("animations", False)
    again = Settings(p)
    assert (again.get("accent"), again.get("lang"), again.get("animations")) == ("#ff7a45", "en", False)


def test_corrupted_file_is_set_aside_and_defaults_used(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{not json", encoding="utf-8")
    s = Settings(str(p))
    assert s.data == DEFAULTS and (tmp_path / "c.json.corrupt").exists() and "corrupted" in s.last_error
    s.set("theme", "light")                                  # и после этого файл снова пишется
    assert json.loads(p.read_text())["theme"] == "light"


def test_non_object_json_is_rejected(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert Settings(str(p)).data == DEFAULTS


def test_invalid_values_are_sanitized(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"theme": "neon", "accent": "red", "lang": "de", "animations": "yes", "x": 1}), encoding="utf-8")
    s = Settings(str(p))
    assert (s.get("theme"), s.get("accent"), s.get("lang"), s.get("animations")) == ("dark", None, "ru", True)
    assert s.get("x") == 1                                   # неизвестные ключи сохраняются


def test_legacy_settings_are_migrated(tmp_path):
    legacy = tmp_path / "settings.json"
    legacy.write_text(json.dumps({"theme": "light", "accent": "#8B7CFF", "animations": False, "language": "en",
                                  "glass_intensity": 48, "socials": {"github": "g"}}), encoding="utf-8")
    s = Settings(str(tmp_path / "config.json"), legacy_path=str(legacy))
    assert (s.get("theme"), s.get("lang"), s.get("animations"), s.get("glass_intensity")) == ("light", "en", False, 48)
    assert (tmp_path / "config.json").exists()               # сразу сохранено в новом формате
    assert legacy.exists()                                   # старый файл не трогаем


def test_existing_config_wins_over_legacy(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"theme": "light"}), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"theme": "dark", "lang": "en"}), encoding="utf-8")
    s = Settings(str(tmp_path / "config.json"), legacy_path=str(tmp_path / "settings.json"))
    assert (s.get("theme"), s.get("lang")) == ("dark", "en")


def test_atomic_save_leaves_no_temp_files(tmp_path):
    s = Settings(str(tmp_path / "c.json"))
    for i in range(5):
        s.set("accent", f"#00000{i}")
    assert sorted(os.listdir(tmp_path)) == ["c.json"]


def test_unwritable_location_does_not_crash(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    s = Settings(str(blocker / "sub" / "c.json"))           # каталог создать нельзя
    s.set("theme", "light")                                  # не должно бросать
    assert s.get("theme") == "light" and s.last_error
