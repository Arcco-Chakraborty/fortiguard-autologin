from unittest.mock import patch, MagicMock
import auth


def test_login_returns_true_on_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_true_on_302():
    mock_resp = MagicMock()
    mock_resp.status_code = 302
    with patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_false_on_non_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_on_network_error():
    import requests
    with patch("auth.requests.post", side_effect=requests.RequestException("timeout")), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_when_no_credentials():
    with patch("auth.load_credentials", return_value=None):
        assert auth.login() is False


def test_login_posts_to_correct_url():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("auth.requests.post", return_value=mock_resp) as mock_post, \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        auth.login()
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == auth.LOGIN_URL
