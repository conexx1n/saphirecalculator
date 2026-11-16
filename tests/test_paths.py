from app.core.paths import config_dir, data_dir


def test_linux_paths_follow_xdg(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.paths.sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    assert config_dir() == tmp_path / "config" / "sapphire-calculator"
    assert data_dir() == tmp_path / "data" / "sapphire-calculator"
