import requests
import urllib3
from credentials import load_credentials

PORTAL_HOST = "https://fw.bits-pilani.ac.in:8090"
LOGIN_PATH = "/fgtauth"
PROBE_URL = "http://connectivitycheck.gstatic.com/generate_204"
VERIFY_SSL = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_magic_token() -> str | None:
    """Fetch a plain HTTP page and extract the magic token from the FortiGuard redirect URL."""
    try:
        response = requests.get(
            PROBE_URL,
            timeout=10,
            allow_redirects=True,
            verify=VERIFY_SSL,
        )
        # If we get redirected to the FortiGuard portal, the final URL contains the magic token
        final_url = response.url
        if LOGIN_PATH in final_url and "?" in final_url:
            return final_url.split("?", 1)[1]
    except requests.RequestException:
        pass
    return None


def login() -> bool:
    creds = load_credentials()
    if not creds:
        return False
    username, password = creds

    magic = _get_magic_token()
    if not magic:
        return False

    try:
        response = requests.post(
            f"{PORTAL_HOST}{LOGIN_PATH}",
            data={
                "magic": magic,
                "Username": username,
                "Password": password,
                "4Tredir": "http://www.google.com/",
            },
            timeout=10,
            allow_redirects=True,
            verify=VERIFY_SSL,
        )
        return response.status_code in (200, 302)
    except requests.RequestException:
        return False
