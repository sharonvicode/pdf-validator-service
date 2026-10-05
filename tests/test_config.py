from app.core.config import get_settings


def test_default_max_size_is_10_mb(monkeypatch):
    monkeypatch.delenv("MAX_FILE_SIZE_MB", raising=False)
    assert get_settings().max_file_size_bytes == 10 * 1024 * 1024


def test_max_size_comes_from_environment(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "2")
    assert get_settings().max_file_size_bytes == 2 * 1024 * 1024
