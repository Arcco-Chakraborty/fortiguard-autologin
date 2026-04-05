from unittest.mock import patch
import pytest
import credentials


def test_save_credentials_stores_username_and_password():
    with patch("credentials.keyring.set_password") as mock_set:
        credentials.save_credentials("alice", "secret")
        mock_set.assert_any_call("fortiguard-autologin", "username", "alice")
        mock_set.assert_any_call("fortiguard-autologin", "password", "secret")


def test_load_credentials_returns_tuple_when_both_exist():
    with patch("credentials.keyring.get_password", side_effect=["alice", "secret"]):
        result = credentials.load_credentials()
        assert result == ("alice", "secret")


def test_load_credentials_returns_none_when_missing():
    with patch("credentials.keyring.get_password", return_value=None):
        result = credentials.load_credentials()
        assert result is None


def test_load_credentials_returns_none_when_only_username_exists():
    with patch("credentials.keyring.get_password", side_effect=["alice", None]):
        result = credentials.load_credentials()
        assert result is None


def test_clear_credentials_deletes_both():
    with patch("credentials.keyring.delete_password") as mock_del:
        credentials.clear_credentials()
        mock_del.assert_any_call("fortiguard-autologin", "username")
        mock_del.assert_any_call("fortiguard-autologin", "password")


def test_clear_credentials_ignores_missing():
    import keyring.errors
    with patch("credentials.keyring.delete_password",
               side_effect=keyring.errors.PasswordDeleteError("not found")):
        credentials.clear_credentials()  # must not raise
