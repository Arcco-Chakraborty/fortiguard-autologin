import re
import logging
import requests
import urllib3
from credentials import load_credentials

log = logging.getLogger(__name__)

PORTAL_HOST = "https://fw.bits-pilani.ac.in:8090"
LOGIN_PATH = "/login"
POST_PATH = "/"
KEEPALIVE_PATH = "/keepalive"
PROBE_URL = "http://connectivitycheck.gstatic.com/generate_204"
VERIFY_SSL = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Reusable session for cookies/keepalive
_session = requests.Session()
_session.verify = VERIFY_SSL
_keepalive_url: str | None = None


def _extract_js_redirect(html: str) -> str | None:
    """Extract URL from a JavaScript window.location redirect."""
    match = re.search(r'window\.location="([^"]+)"', html)
    if match:
        return match.group(1)
    return None


def _get_login_page() -> tuple[str, str] | None:
    """Probe an HTTP URL; if FortiGuard intercepts, follow JS redirect and return (login_page_url, html)."""
    try:
        # Step 1: probe — FortiGuard returns 200 with a JS redirect, not an HTTP 302
        resp = _session.get(PROBE_URL, timeout=10, allow_redirects=True)
        log.debug(f"Probe status={resp.status_code} url={resp.url}")

        # Check if we got a JS redirect to the portal
        js_url = _extract_js_redirect(resp.text)
        if js_url and PORTAL_HOST in js_url:
            log.info(f"JS redirect to portal: {js_url}")
            # Step 2: follow the JS redirect to get the actual login page
            login_resp = _session.get(js_url, timeout=10, allow_redirects=True)
            login_url = login_resp.url
            log.info(f"Login page loaded: {login_url}")
            return login_url, login_resp.text

    except requests.RequestException as e:
        log.warning(f"Probe failed: {e}")
    return None


def _extract_magic(html: str) -> str | None:
    """Extract the hidden 'magic' input value from the login page HTML."""
    match = re.search(r'name=["\']?magic["\']?\s+value=["\']?([^"\'>\s]+)', html)
    if not match:
        # try reversed attribute order: value before name
        match = re.search(r'value=["\']?([^"\'>\s]+)["\']?\s+name=["\']?magic', html)
    if match:
        token = match.group(1)
        log.info(f"Magic token extracted: {token[:8]}...")
        return token
    log.warning("Could not find magic token in login page HTML")
    return None


def _extract_keepalive_url(html: str) -> str | None:
    """Try to find a keepalive URL in the post-login response."""
    match = re.search(r'(/keepalive\?[a-fA-F0-9]+)', html)
    if match:
        url = f"{PORTAL_HOST}{match.group(1)}"
        log.info(f"Keepalive URL found: {url}")
        return url
    return None


def login() -> bool:
    """Perform the full FortiGuard login flow. Returns True on success."""
    global _keepalive_url

    creds = load_credentials()
    if not creds:
        log.warning("No credentials available")
        return False
    username, password = creds

    # Step 1: hit an HTTP URL, follow redirect to login page
    result = _get_login_page()
    if not result:
        log.info("No captive portal redirect — may already be online")
        return False
    login_url, html = result

    # Step 2: extract the magic token from the login page HTML
    magic = _extract_magic(html)
    if not magic:
        return False

    # Step 3: POST credentials to the portal root
    try:
        resp = _session.post(
            f"{PORTAL_HOST}{POST_PATH}",
            data={
                "magic": magic,
                "username": username,
                "password": password,
                "4Tredir": login_url,
            },
            timeout=10,
            allow_redirects=True,
        )
        success = resp.status_code in (200, 302)
        log.info(f"Login POST status={resp.status_code} success={success}")

        # Try to grab keepalive URL from response
        if success:
            ka = _extract_keepalive_url(resp.text)
            if ka:
                _keepalive_url = ka

        return success
    except requests.RequestException as e:
        log.warning(f"Login POST failed: {e}")
        return False


def keepalive() -> bool:
    """Ping the keepalive endpoint to maintain the session."""
    global _keepalive_url
    if not _keepalive_url:
        return False
    try:
        resp = _session.get(_keepalive_url, timeout=10)
        ok = resp.status_code == 200
        log.debug(f"Keepalive status={resp.status_code}")

        # The keepalive response may contain an updated keepalive URL
        if ok:
            ka = _extract_keepalive_url(resp.text)
            if ka:
                _keepalive_url = ka

        return ok
    except requests.RequestException as e:
        log.debug(f"Keepalive failed: {e}")
        return False
