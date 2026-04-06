from unittest.mock import patch, MagicMock
import auth


JS_REDIRECT_HTML = '''
<html><body><script language="JavaScript">window.location="https://fw.bits-pilani.ac.in:8090/fgtauth?aabb1122";</script></body></html>
'''

LOGIN_PAGE_HTML = '''
<html><body>
<form method="POST" action="/">
<input type="hidden" name="magic" value="abc123def456">
<input type="text" name="username">
<input type="password" name="password">
<input type="hidden" name="4Tredir" value="https://fw.bits-pilani.ac.in:8090/login?aaaa">
</form>
</body></html>
'''

KEEPALIVE_HTML = '''
<html><body>
<script>window.location="/keepalive?02020c0700050f05";</script>
</body></html>
'''


def _mock_resp(url, text="", status=200):
    mock = MagicMock()
    mock.url = url
    mock.status_code = status
    mock.text = text
    return mock


# --- _extract_js_redirect ---

def test_extract_js_redirect_finds_url():
    assert auth._extract_js_redirect(JS_REDIRECT_HTML) == "https://fw.bits-pilani.ac.in:8090/fgtauth?aabb1122"


def test_extract_js_redirect_returns_none_for_normal_page():
    assert auth._extract_js_redirect("<html><body>hello</body></html>") is None


# --- _get_login_page ---

def test_get_login_page_follows_js_redirect():
    probe_resp = _mock_resp("http://connectivitycheck.gstatic.com/generate_204", JS_REDIRECT_HTML)
    login_resp = _mock_resp("https://fw.bits-pilani.ac.in:8090/login?xyz", LOGIN_PAGE_HTML)
    with patch.object(auth._session, "get", side_effect=[probe_resp, login_resp]):
        result = auth._get_login_page()
        assert result is not None
        url, html = result
        assert url == "https://fw.bits-pilani.ac.in:8090/login?xyz"
        assert "magic" in html


def test_get_login_page_returns_none_when_not_redirected():
    resp = _mock_resp("http://connectivitycheck.gstatic.com/generate_204", "")
    with patch.object(auth._session, "get", return_value=resp):
        assert auth._get_login_page() is None


def test_get_login_page_returns_none_on_network_error():
    import requests
    with patch.object(auth._session, "get", side_effect=requests.RequestException("timeout")):
        assert auth._get_login_page() is None


# --- _extract_magic ---

def test_extract_magic_finds_token():
    assert auth._extract_magic(LOGIN_PAGE_HTML) == "abc123def456"


def test_extract_magic_reversed_attrs():
    html = '<input value="tok999" name="magic">'
    assert auth._extract_magic(html) == "tok999"


def test_extract_magic_returns_none_when_missing():
    assert auth._extract_magic("<html><body>no form here</body></html>") is None


# --- login ---

def test_login_returns_true_on_200():
    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.text = ""
    with patch("auth._get_login_page", return_value=("https://fw.bits-pilani.ac.in:8090/login?abc", LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", return_value=post_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_true_on_302():
    post_resp = MagicMock()
    post_resp.status_code = 302
    post_resp.text = ""
    with patch("auth._get_login_page", return_value=("https://fw.bits-pilani.ac.in:8090/login?abc", LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", return_value=post_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is True


def test_login_returns_false_on_401():
    post_resp = MagicMock()
    post_resp.status_code = 401
    post_resp.text = ""
    with patch("auth._get_login_page", return_value=("https://fw.bits-pilani.ac.in:8090/login?abc", LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", return_value=post_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_on_network_error():
    import requests
    with patch("auth._get_login_page", return_value=("https://fw.bits-pilani.ac.in:8090/login?abc", LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", side_effect=requests.RequestException("timeout")), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_returns_false_when_no_credentials():
    with patch("auth.load_credentials", return_value=None):
        assert auth.login() is False


def test_login_returns_false_when_no_portal_redirect():
    with patch("auth._get_login_page", return_value=None), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        assert auth.login() is False


def test_login_posts_correct_fields():
    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.text = ""
    login_url = "https://fw.bits-pilani.ac.in:8090/login?abc"
    with patch("auth._get_login_page", return_value=(login_url, LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", return_value=post_resp) as mock_post, \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        auth.login()
        data = mock_post.call_args[1]["data"]
        assert data["magic"] == "abc123def456"
        assert data["username"] == "alice"
        assert data["password"] == "secret"
        assert data["4Tredir"] == login_url


# --- keepalive ---

def test_keepalive_returns_false_when_no_url():
    auth._keepalive_url = None
    assert auth.keepalive() is False


def test_keepalive_pings_url():
    auth._keepalive_url = "https://fw.bits-pilani.ac.in:8090/keepalive?aaa"
    resp = MagicMock()
    resp.status_code = 200
    resp.text = ""
    with patch.object(auth._session, "get", return_value=resp) as mock_get:
        assert auth.keepalive() is True
        mock_get.assert_called_once()
    auth._keepalive_url = None


def test_login_extracts_keepalive_url_from_response():
    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.text = KEEPALIVE_HTML
    with patch("auth._get_login_page", return_value=("https://fw.bits-pilani.ac.in:8090/login?abc", LOGIN_PAGE_HTML)), \
         patch.object(auth._session, "post", return_value=post_resp), \
         patch("auth.load_credentials", return_value=("alice", "secret")):
        auth.login()
        assert auth._keepalive_url == "https://fw.bits-pilani.ac.in:8090/keepalive?02020c0700050f05"
    auth._keepalive_url = None
