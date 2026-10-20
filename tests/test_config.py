import pytest

from app.core.config import Settings, get_settings


def test_default_max_size_is_10_mb(monkeypatch):
    monkeypatch.delenv("MAX_FILE_SIZE_MB", raising=False)
    assert get_settings().max_file_size_bytes == 10 * 1024 * 1024


def test_max_size_comes_from_environment(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "2")
    assert get_settings().max_file_size_bytes == 2 * 1024 * 1024


@pytest.mark.parametrize("value", ["abc", "1.5", "", "0", "-1"])
def test_invalid_max_size_from_environment_is_rejected(monkeypatch, value):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", value)
    with pytest.raises(ValueError, match="MAX_FILE_SIZE_MB"):
        get_settings()


@pytest.mark.parametrize("value", [0, -1])
def test_settings_reject_non_positive_max_size(value):
    with pytest.raises(ValueError, match="MAX_FILE_SIZE_MB"):
        Settings(max_file_size_mb=value)
