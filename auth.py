import requests
import urllib3
from credentials import load_credentials

LOGIN_URL = "http://fw.bits-pilani.ac.in:8090/fgtauth"
USERNAME_FIELD = "Username"
PASSWORD_FIELD = "Password"
VERIFY_SSL = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def login() -> bool:
    creds = load_credentials()
    if not creds:
        return False
    username, password = creds
    try:
        response = requests.post(
            LOGIN_URL,
            data={USERNAME_FIELD: username, PASSWORD_FIELD: password},
            timeout=10,
            allow_redirects=True,
            verify=VERIFY_SSL,
        )
        return response.status_code in (200, 302)
    except requests.RequestException:
        return False
