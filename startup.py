import sys
import os
import platform

APP_NAME = "FortiGuardAutoLogin"


def _get_launch_cmd() -> str:
    """Build the command string to launch this app."""
    if getattr(sys, "frozen", False):
        return sys.executable
    else:
        script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        if platform.system() == "Windows":
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            return f'"{pythonw}" "{script}"'
        return f'"{sys.executable}" "{script}"'


# --- Windows ---

def _win_enable():
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_launch_cmd())


def _win_disable():
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def _win_is_enabled() -> bool:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


# --- macOS ---

def _mac_plist_path() -> str:
    return os.path.expanduser(f"~/Library/LaunchAgents/com.{APP_NAME}.plist")


def _mac_enable():
    import plistlib
    cmd = _get_launch_cmd()
    # Split quoted command into args
    args = [a.strip('"') for a in cmd.split('" "')]
    plist = {
        "Label": f"com.{APP_NAME}",
        "ProgramArguments": args,
        "RunAtLoad": True,
        "KeepAlive": False,
    }
    path = _mac_plist_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        plistlib.dump(plist, f)


def _mac_disable():
    path = _mac_plist_path()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def _mac_is_enabled() -> bool:
    return os.path.exists(_mac_plist_path())


# --- Public API ---

_IS_MAC = platform.system() == "Darwin"


def enable_startup() -> None:
    (_mac_enable if _IS_MAC else _win_enable)()


def disable_startup() -> None:
    (_mac_disable if _IS_MAC else _win_disable)()


def is_startup_enabled() -> bool:
    return (_mac_is_enabled if _IS_MAC else _win_is_enabled)()
