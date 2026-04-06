import winreg
import sys

APP_NAME = "FortiGuardAutoLogin"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def enable_startup() -> None:
    import os
    # When frozen (PyInstaller exe), sys.executable is the exe itself.
    # When running as a script, we need pythonw + the script path.
    if getattr(sys, "frozen", False):
        cmd = f'"{sys.executable}"'
    else:
        script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        cmd = f'"{pythonw}" "{script}"'

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)


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
