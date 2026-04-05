import keyring
import keyring.errors

SERVICE_NAME = "fortiguard-autologin"


def save_credentials(username: str, password: str) -> None:
    keyring.set_password(SERVICE_NAME, "username", username)
    keyring.set_password(SERVICE_NAME, "password", password)


def load_credentials() -> tuple[str, str] | None:
    username = keyring.get_password(SERVICE_NAME, "username")
    password = keyring.get_password(SERVICE_NAME, "password")
    if username and password:
        return username, password
    return None


def clear_credentials() -> None:
    for field in ("username", "password"):
        try:
            keyring.delete_password(SERVICE_NAME, field)
        except keyring.errors.PasswordDeleteError:
            pass
