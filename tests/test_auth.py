from unittest.mock import patch, MagicMock
import auth


def _mock_redirect(url):
    mock_resp = MagicMock()
    mock_resp.url = url
    mock_resp.status_code = 200
    return mock_resp


def test_get_magic_token_extracts_token_from_redirect():
    with patch("auth.requests.get", return_value=_mock_redirect("https://fw.bits-pilani.ac.in:8090/fgtauth?abc123")):
        assert auth._get_magic_token() == "abc123"


def test_get_magic_token_returns_none_when_not_redirected():
    with patch("auth.requests.get", return_value=_mock_redirect("http://connectivitycheck.gstatic.com/generate_204")):
        assert auth._get_magic_token() is None


def test_get_magic_token_returns_none_on_network_error():
    import requests
    with patch("auth.requests.get", side_effect=requests.RequestException("timeout")):
        assert auth._get_magic_token() is None


def test_login_returns_true_on_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("auth._get_magic_token", return_value="abc123"), \
         patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_true_on_302():
    mock_resp = MagicMock()
    mock_resp.status_code = 302
    with patch("auth._get_magic_token", return_value="abc123"), \
         patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_false_on_non_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("auth._get_magic_token", return_value="abc123"), \
         patch("auth.requests.post", return_value=mock_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_on_network_error():
    import requests
    with patch("auth._get_magic_token", return_value="abc123"), \
         patch("auth.requests.post", side_effect=requests.RequestException("timeout")), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_when_no_credentials():
    with patch("auth.load_credentials", return_value=None):
        assert auth.login() is False


def test_login_returns_false_when_no_magic_token():
    with patch("auth._get_magic_token", return_value=None), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_posts_magic_token_with_credentials():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("auth._get_magic_token", return_value="abc123"), \
         patch("auth.requests.post", return_value=mock_resp) as mock_post, \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        auth.login()
        data = mock_post.call_args[1]["data"]
        assert data["magic"] == "abc123"
        assert data["Username"] == "alice"
        assert data["Password"] == "secret"
