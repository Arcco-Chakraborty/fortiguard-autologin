import logging
import sys
import os

# Set up logging before any other imports
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "fortiguard.log")),
    ],
)
log = logging.getLogger(__name__)

from credentials import load_credentials
from startup import enable_startup
from setup_ui import show_setup_window
from monitor import NetworkMonitor
from tray import create_tray, run_tray, set_connected, set_reconnecting
from auth import login, keepalive


def main() -> None:
    log.info("=== FortiGuard Auto-Login starting ===")

    # --test flag: try auth once and exit (for debugging)
    if "--test" in sys.argv:
        _test_auth()
        return

    if not load_credentials():
        log.info("No credentials found, showing setup window")
        show_setup_window(on_save=_start_app)
    else:
        log.info("Credentials found, starting app")
        _start_app()


def _test_auth() -> None:
    """Quick auth test — prints results to console and log."""
    from auth import _get_login_page, _extract_magic
    print("Testing FortiGuard authentication...")

    creds = load_credentials()
    if not creds:
        print("ERROR: No credentials saved. Run the app normally first to enter them.")
        return

    print(f"Credentials found for user: {creds[0]}")

    print("Probing for captive portal redirect...")
    result = _get_login_page()
    if not result:
        print("No captive portal redirect — you may already be connected, or not on the BITS WiFi.")
        return

    login_url, html = result
    print(f"Login page: {login_url}")

    magic = _extract_magic(html)
    if not magic:
        print("ERROR: Could not extract magic token from login page HTML.")
        print("Page HTML (first 500 chars):")
        print(html[:500])
        return

    print(f"Magic token: {magic[:8]}...")
    print("Attempting login...")
    ok = login()
    print(f"Login {'SUCCEEDED' if ok else 'FAILED'}")


def _start_app() -> None:
    monitor_holder: list = [None]

    def on_disconnected():
        set_reconnecting(icon)
        log.info("Disconnected — attempting login")
        result = login()
        log.info(f"Login attempt result: {result}")

    def on_reconnected():
        set_connected(icon)

    def on_quit(ic):
        log.info("User quit")
        if monitor_holder[0]:
            monitor_holder[0].stop()
        ic.stop()

    def on_ready(ic):
        """Called by pystray after icon is visible — safe to start monitor now."""
        log.info("Tray icon ready, starting network monitor")

        def on_keepalive():
            keepalive()

        monitor = NetworkMonitor(
            on_disconnected=on_disconnected,
            on_reconnected=on_reconnected,
            on_keepalive=on_keepalive,
        )
        monitor_holder[0] = monitor
        monitor.start()

    try:
        enable_startup()
        log.info("Startup registration updated")
    except Exception as e:
        log.warning(f"Could not register startup: {e}")

    icon = create_tray(on_quit=on_quit, on_ready=on_ready)
    run_tray(icon)  # blocks until quit
    log.info("App exiting")


if __name__ == "__main__":
    main()
