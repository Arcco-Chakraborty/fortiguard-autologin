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
