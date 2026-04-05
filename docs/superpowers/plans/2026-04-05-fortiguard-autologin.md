# FortiGuard WiFi Auto-Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows system-tray app that silently monitors WiFi connectivity and re-authenticates against a FortiGuard captive portal whenever the connection drops.

**Architecture:** A single Python process runs two concurrent units — `pystray` owns the main thread (required by the library) and drives the tray icon/menu, while a daemon thread runs the network monitor loop. When the monitor detects loss of internet, it calls the auth handler which POSTs credentials to the FortiGuard login endpoint. Credentials are stored in Windows Credential Manager via `keyring`; startup registration uses the Windows registry via `winreg`.

**Tech Stack:** Python 3.11+, `requests`, `pystray`, `Pillow`, `keyring`, `tkinter` (stdlib), `winreg` (stdlib), PyInstaller for packaging, GitHub Actions for CI releases.

---

## File Map

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point: first-run check → launch tray + monitor |
| `credentials.py` | Read/write credentials via Windows Credential Manager |
| `startup.py` | Read/write Windows startup registry key |
| `auth.py` | HTTP POST to FortiGuard login endpoint |
| `monitor.py` | Background thread: poll connectivity, trigger auth on failure |
| `tray.py` | pystray icon, menu, icon image generation |
| `setup_ui.py` | tkinter first-run credentials window |
| `tests/test_credentials.py` | Unit tests for credentials.py |
| `tests/test_startup.py` | Unit tests for startup.py |
| `tests/test_auth.py` | Unit tests for auth.py |
| `tests/test_monitor.py` | Unit tests for monitor.py |
| `requirements.txt` | Runtime + dev dependencies |
| `.github/workflows/build.yml` | PyInstaller build + GitHub Release upload |
| `README.md` | 3-step user instructions |

---

## Task 1: Project Scaffold

**Files:**
- Create: `D:/Projects/fortiguard-autologin/requirements.txt`
- Create: `D:/Projects/fortiguard-autologin/.gitignore`
- Create: `D:/Projects/fortiguard-autologin/tests/__init__.py`

- [ ] **Step 1: Create project root and initialize git**

```bash
cd D:/Projects/fortiguard-autologin
git init
```

- [ ] **Step 2: Write requirements.txt**

```
requests>=2.31.0
pystray>=0.19.5
Pillow>=10.0.0
keyring>=24.0.0
pyinstaller>=6.0.0
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
dist/
build/
*.spec
.venv/
```

- [ ] **Step 4: Create tests package**

```bash
mkdir tests
touch tests/__init__.py
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 6: Verify pytest runs (no tests yet = OK)**

```bash
pytest tests/ -v
```
Expected: `no tests ran` or `0 passed`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore tests/__init__.py
git commit -m "chore: project scaffold"
```

---

## Task 2: Credentials Module

**Files:**
- Create: `credentials.py`
- Create: `tests/test_credentials.py`

- [ ] **Step 1: Write failing tests**

`tests/test_credentials.py`:
```python
from unittest.mock import patch, call
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_credentials.py -v
```
Expected: `ModuleNotFoundError: No module named 'credentials'`

- [ ] **Step 3: Implement credentials.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_credentials.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add credentials.py tests/test_credentials.py
git commit -m "feat: credentials read/write via Windows Credential Manager"
```

---

## Task 3: Startup Module

**Files:**
- Create: `startup.py`
- Create: `tests/test_startup.py`

- [ ] **Step 1: Write failing tests**

`tests/test_startup.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_startup.py -v
```
Expected: `ModuleNotFoundError: No module named 'startup'`

- [ ] **Step 3: Implement startup.py**

```python
import winreg
import sys

APP_NAME = "FortiGuardAutoLogin"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def enable_startup() -> None:
    exe_path = sys.executable
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')


def disable_startup() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def is_startup_enabled() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_startup.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add startup.py tests/test_startup.py
git commit -m "feat: Windows startup registry enable/disable"
```

---

## Task 4: Capture FortiGuard Endpoint

**This task is manual — no code yet. Do it before implementing auth.py.**

- [ ] **Step 1: Connect to college WiFi (before logging in)**

- [ ] **Step 2: Open browser → navigate to any HTTP site (e.g. `http://neverssl.com`)**

You'll be redirected to the FortiGuard login page.

- [ ] **Step 3: Open DevTools (F12) → Network tab → check "Preserve log"**

- [ ] **Step 4: Enter credentials and click Login**

- [ ] **Step 5: Find the POST request in the Network tab**

Look for a request to a URL like `https://<ip>/fgtauth` or `https://<ip>/logincheck`. Click it.

- [ ] **Step 6: Record these values (you'll need them for auth.py)**

- **Login URL**: the full URL from the request
- **Username field name**: from the Form Data section (e.g. `username`, `magic`, `4Tredir`)
- **Password field name**: from the Form Data section (e.g. `password`)
- **Any other required fields**: copy all form fields shown

- [ ] **Step 7: Note whether the server uses a self-signed TLS certificate**

If browser shows a security warning before the login page, set `VERIFY_SSL = False` in auth.py.

---

## Task 5: Auth Module

**Files:**
- Create: `auth.py`
- Create: `tests/test_auth.py`

Replace `LOGIN_URL`, `USERNAME_FIELD`, `PASSWORD_FIELD` with values captured in Task 4.

- [ ] **Step 1: Write failing tests**

`tests/test_auth.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth.py -v
```
Expected: `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: Implement auth.py**

Fill in `LOGIN_URL`, `USERNAME_FIELD`, `PASSWORD_FIELD` from Task 4.

```python
import requests
import urllib3
from credentials import load_credentials

# Fill in from Task 4 — browser dev tools capture
LOGIN_URL = "https://REPLACE_WITH_YOUR_FORTIGATE_IP/fgtauth"
USERNAME_FIELD = "username"   # replace with actual form field name
PASSWORD_FIELD = "password"   # replace with actual form field name
VERIFY_SSL = False            # set True if portal has valid cert

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_auth.py -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add auth.py tests/test_auth.py
git commit -m "feat: FortiGuard HTTP login handler"
```

---

## Task 6: Network Monitor

**Files:**
- Create: `monitor.py`
- Create: `tests/test_monitor.py`

- [ ] **Step 1: Write failing tests**

`tests/test_monitor.py`:
```python
from unittest.mock import patch, MagicMock, call
import threading
import time
import monitor


def test_is_connected_returns_true_on_success():
    m = monitor.NetworkMonitor(on_disconnected=lambda: None, on_reconnected=lambda: None)
    with patch("monitor.requests.head"):
        assert m._is_connected() is True


def test_is_connected_returns_false_on_exception():
    import requests
    m = monitor.NetworkMonitor(on_disconnected=lambda: None, on_reconnected=lambda: None)
    with patch("monitor.requests.head", side_effect=requests.RequestException):
        assert m._is_connected() is False


def test_on_disconnected_called_when_connection_drops():
    disconnected = []
    m = monitor.NetworkMonitor(
        on_disconnected=lambda: disconnected.append(True),
        on_reconnected=lambda: None,
    )
    import requests
    # First call fails (disconnected), then succeeds
    responses = [requests.RequestException("fail"), MagicMock()]
    with patch("monitor.requests.head", side_effect=responses), \
         patch("monitor.POLL_INTERVAL", 0), \
         patch("monitor.BACKOFF_SEQUENCE", [0]):
        m.start()
        time.sleep(0.1)
        m.stop()
        m._thread.join(timeout=1)
    assert len(disconnected) >= 1


def test_on_reconnected_called_after_recovery():
    reconnected = []
    import requests
    # Fail once, then succeed twice (triggers reconnect on second success)
    call_count = {"n": 0}
    def side_effect(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise requests.RequestException("fail")
    m = monitor.NetworkMonitor(
        on_disconnected=lambda: None,
        on_reconnected=lambda: reconnected.append(True),
    )
    with patch("monitor.requests.head", side_effect=side_effect), \
         patch("monitor.POLL_INTERVAL", 0), \
         patch("monitor.BACKOFF_SEQUENCE", [0]):
        m.start()
        time.sleep(0.2)
        m.stop()
        m._thread.join(timeout=1)
    assert len(reconnected) >= 1


def test_stop_terminates_thread():
    m = monitor.NetworkMonitor(on_disconnected=lambda: None, on_reconnected=lambda: None)
    with patch("monitor.requests.head"), patch("monitor.POLL_INTERVAL", 0):
        m.start()
        time.sleep(0.05)
        m.stop()
        m._thread.join(timeout=2)
    assert not m._thread.is_alive()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_monitor.py -v
```
Expected: `ModuleNotFoundError: No module named 'monitor'`

- [ ] **Step 3: Implement monitor.py**

```python
import threading
import time
import requests

CHECK_URL = "https://www.google.com"
POLL_INTERVAL = 30
BACKOFF_SEQUENCE = [5, 15, 30, 60]


class NetworkMonitor:
    def __init__(self, on_disconnected, on_reconnected):
        self.on_disconnected = on_disconnected
        self.on_reconnected = on_reconnected
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _is_connected(self) -> bool:
        try:
            requests.head(CHECK_URL, timeout=5)
            return True
        except requests.RequestException:
            return False

    def _run(self) -> None:
        was_connected = True
        while not self._stop_event.is_set():
            connected = self._is_connected()
            if not connected:
                was_connected = False
                self.on_disconnected()
                for backoff in BACKOFF_SEQUENCE:
                    if self._stop_event.wait(backoff):
                        return
                    if self._is_connected():
                        break
            elif not was_connected:
                was_connected = True
                self.on_reconnected()
            self._stop_event.wait(POLL_INTERVAL)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_monitor.py -v
```
Expected: 5 passed

- [ ] **Step 5: Run all tests to check nothing broke**

```bash
pytest tests/ -v
```
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add monitor.py tests/test_monitor.py
git commit -m "feat: background network monitor with backoff retry"
```

---

## Task 7: Setup UI

**Files:**
- Create: `setup_ui.py`

No unit tests for the tkinter window (requires display). Manual verification in Task 10.

- [ ] **Step 1: Implement setup_ui.py**

```python
import tkinter as tk
from tkinter import messagebox
from credentials import save_credentials, load_credentials


def show_setup_window(on_save=None) -> None:
    root = tk.Tk()
    root.title("FortiGuard Auto-Login Setup")
    root.geometry("350x210")
    root.resizable(False, False)
    root.eval("tk::PlaceWindow . center")

    tk.Label(root, text="College WiFi Credentials", font=("Arial", 12, "bold")).pack(
        pady=(20, 10)
    )

    frame = tk.Frame(root)
    frame.pack(padx=20)

    tk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e", pady=6)
    username_var = tk.StringVar()
    tk.Entry(frame, textvariable=username_var, width=25).grid(row=0, column=1, padx=6)

    tk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e", pady=6)
    password_var = tk.StringVar()
    tk.Entry(frame, textvariable=password_var, show="*", width=25).grid(
        row=1, column=1, padx=6
    )

    existing = load_credentials()
    if existing:
        username_var.set(existing[0])

    def _save():
        username = username_var.get().strip()
        password = password_var.get()
        if not username or not password:
            messagebox.showerror("Error", "Both fields are required.", parent=root)
            return
        save_credentials(username, password)
        root.destroy()
        if on_save:
            on_save()

    tk.Button(root, text="Save & Start", command=_save, width=15).pack(pady=15)
    root.mainloop()
```

- [ ] **Step 2: Commit**

```bash
git add setup_ui.py
git commit -m "feat: tkinter first-run credentials setup window"
```

---

## Task 8: System Tray

**Files:**
- Create: `tray.py`

No unit tests for pystray (requires display). Manual verification in Task 10.

- [ ] **Step 1: Implement tray.py**

```python
import pystray
from PIL import Image, ImageDraw
from startup import enable_startup, disable_startup, is_startup_enabled
from setup_ui import show_setup_window


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


ICON_CONNECTED = _make_icon("#22c55e")
ICON_RECONNECTING = _make_icon("#eab308")


def create_tray(on_quit) -> pystray.Icon:
    _state = {"connected": True}

    def status_text(item):
        return "Status: Connected" if _state["connected"] else "Status: Reconnecting..."

    def startup_text(item):
        return "Disable auto-start" if is_startup_enabled() else "Enable auto-start"

    def toggle_startup(icon, item):
        if is_startup_enabled():
            disable_startup()
        else:
            enable_startup()

    def update_credentials(icon, item):
        show_setup_window()

    def quit_app(icon, item):
        on_quit(icon)

    menu = pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.MenuItem("Update credentials", update_credentials),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(startup_text, toggle_startup),
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon(
        "fortiguard", ICON_CONNECTED, "FortiGuard Auto-Login — Connected", menu
    )
    icon._state = _state
    return icon


def set_connected(icon: pystray.Icon) -> None:
    icon._state["connected"] = True
    icon.icon = ICON_CONNECTED
    icon.title = "FortiGuard Auto-Login — Connected"


def set_reconnecting(icon: pystray.Icon) -> None:
    icon._state["connected"] = False
    icon.icon = ICON_RECONNECTING
    icon.title = "FortiGuard Auto-Login — Reconnecting..."
```

- [ ] **Step 2: Commit**

```bash
git add tray.py
git commit -m "feat: system tray icon with status and menu"
```

---

## Task 9: Entry Point

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

```python
from credentials import load_credentials
from startup import enable_startup
from setup_ui import show_setup_window
from monitor import NetworkMonitor
from tray import create_tray, set_connected, set_reconnecting
from auth import login


def main() -> None:
    if not load_credentials():
        show_setup_window(on_save=_start_app)
    else:
        _start_app()


def _start_app() -> None:
    # monitor_holder lets on_quit reference monitor before it's assigned
    monitor_holder: list = [None]

    def on_disconnected():
        set_reconnecting(icon)
        login()

    def on_reconnected():
        set_connected(icon)

    def on_quit(ic):
        monitor_holder[0].stop()
        ic.stop()

    enable_startup()
    # icon must be created before monitor starts to avoid a race where
    # on_disconnected is called before icon is assigned
    icon = create_tray(on_quit=on_quit)
    monitor = NetworkMonitor(on_disconnected=on_disconnected, on_reconnected=on_reconnected)
    monitor_holder[0] = monitor
    monitor.start()
    icon.run()  # blocks until quit


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests one final time**

```bash
pytest tests/ -v
```
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main entry point — first-run setup and tray+monitor loop"
```

---

## Task 10: Manual End-to-End Verification

- [ ] **Step 1: First-run test — run with no saved credentials**

```bash
python main.py
```
Expected: setup window appears

- [ ] **Step 2: Enter credentials and click Save & Start**

Expected: window closes, tray icon (green dot) appears in system tray

- [ ] **Step 3: Verify startup registration**

Open Task Manager → Startup Apps — "FortiGuardAutoLogin" should appear.

- [ ] **Step 4: Right-click tray icon**

Expected: menu shows Status / Update credentials / Disable auto-start / Quit

- [ ] **Step 5: Click "Disable auto-start" then re-open menu**

Expected: item now says "Enable auto-start"

- [ ] **Step 6: Simulate connectivity loss**

Disable WiFi adapter (or block `google.com` in Windows Firewall), wait ~35 seconds.
Expected: tray icon turns yellow.

- [ ] **Step 7: Re-enable connectivity**

Expected: tray icon turns green within 30s.

- [ ] **Step 8: Reboot**

Expected: app auto-starts, green tray icon visible with no setup window.

---

## Task 11: PyInstaller Build

**Files:**
- No new source files

- [ ] **Step 1: Build the exe**

```bash
pyinstaller --onefile --windowed --name FortiGuardAutoLogin main.py
```

- [ ] **Step 2: Verify dist/FortiGuardAutoLogin.exe exists**

```bash
ls dist/
```

- [ ] **Step 3: Run the exe on this machine**

Double-click `dist/FortiGuardAutoLogin.exe` — same behavior as `python main.py`.

- [ ] **Step 4: Test on a machine without Python installed (optional but ideal)**

Copy `dist/FortiGuardAutoLogin.exe` to another Windows machine — must run with no Python required.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "build: verified PyInstaller single-file exe"
```

---

## Task 12: GitHub Actions CI

**Files:**
- Create: `.github/workflows/build.yml`

- [ ] **Step 1: Write build.yml**

`.github/workflows/build.yml`:
```yaml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Build exe
        run: pyinstaller --onefile --windowed --name FortiGuardAutoLogin main.py

      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/FortiGuardAutoLogin.exe
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: PyInstaller build and release on tag push"
```

> **Later, when ready to publish:** Create a repo on your GitHub account, then:
> ```bash
> git remote add origin https://github.com/YOUR_USERNAME/fortiguard-autologin.git
> git push -u origin main
> git tag v1.0.0
> git push origin v1.0.0
> ```
> GitHub Actions will build the `.exe` and attach it to the release automatically.

---

## Task 13: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# FortiGuard Auto-Login

Automatically re-authenticates you to your college's FortiGuard WiFi captive portal whenever the connection drops. Runs silently in the background.

## Install

1. Download `FortiGuardAutoLogin.exe` from [Releases](../../releases/latest)
2. Double-click it
3. Enter your college WiFi username and password → click **Save & Start**

That's it. The app runs in the background and logs you back in automatically. It will start itself when you boot your laptop.

## Tray Icon

Right-click the icon in your system tray to:
- Check connection status
- Update credentials
- Enable/disable auto-start
- Quit

## Green = Connected · Yellow = Reconnecting
```

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add user-facing README with 3-step install"
git push
```
