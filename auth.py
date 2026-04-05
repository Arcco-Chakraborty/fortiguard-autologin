import requests
import urllib3
from credentials import load_credentials

# TODO: Fill in after capturing from browser dev tools (Task 4)
# See README for capture instructions
LOGIN_URL = "https://REPLACE_WITH_YOUR_FORTIGATE_IP/fgtauth"
USERNAME_FIELD = "username"   # replace with actual form field name
PASSWORD_FIELD = "password"   # replace with actual form field name
VERIFY_SSL = False            # set True if portal has valid TLS cert

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
