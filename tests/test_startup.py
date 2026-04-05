from unittest.mock import patch, MagicMock, call
import startup


def test_enable_startup_writes_registry_value():
    mock_key = MagicMock()
    with patch("startup.winreg.OpenKey", return_value=mock_key.__enter__.return_value), \
         patch("startup.winreg.SetValueEx") as mock_set, \
         patch("startup.sys.executable", "C:/path/app.exe"):
        startup.enable_startup()
        mock_set.assert_called_once()
        args = mock_set.call_args[0]
        assert args[1] == "FortiGuardAutoLogin"
        assert "C:/path/app.exe" in args[4]


def test_disable_startup_deletes_registry_value():
    mock_key = MagicMock()
    with patch("startup.winreg.OpenKey", return_value=mock_key.__enter__.return_value), \
         patch("startup.winreg.DeleteValue") as mock_del:
        startup.disable_startup()
        mock_del.assert_called_once()
        assert mock_del.call_args[0][1] == "FortiGuardAutoLogin"


def test_disable_startup_ignores_missing_key():
    with patch("startup.winreg.OpenKey", side_effect=FileNotFoundError):
        startup.disable_startup()  # must not raise


def test_is_startup_enabled_returns_true_when_key_exists():
    mock_key = MagicMock()
    with patch("startup.winreg.OpenKey", return_value=mock_key.__enter__.return_value), \
         patch("startup.winreg.QueryValueEx", return_value=("value", 1)):
        assert startup.is_startup_enabled() is True


def test_is_startup_enabled_returns_false_when_key_missing():
    with patch("startup.winreg.OpenKey", side_effect=FileNotFoundError):
        assert startup.is_startup_enabled() is False
