import threading
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
