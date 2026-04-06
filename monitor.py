import logging
import time
import threading
import requests

log = logging.getLogger(__name__)

CHECK_URL = "https://www.google.com"
POLL_INTERVAL = 10
BACKOFF_SEQUENCE = [3, 5, 10, 30]
KEEPALIVE_INTERVAL = 2 * 60 * 60  # 2 hours


class NetworkMonitor:
    def __init__(self, on_disconnected, on_reconnected, on_keepalive=None):
        self.on_disconnected = on_disconnected
        self.on_reconnected = on_reconnected
        self.on_keepalive = on_keepalive
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_keepalive = 0.0

    def start(self) -> None:
        log.info("Network monitor started (poll=%ds, keepalive=%ds)", POLL_INTERVAL, KEEPALIVE_INTERVAL)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _is_connected(self) -> bool:
        try:
            requests.head(CHECK_URL, timeout=5)
            return True
        except requests.RequestException:
            return False

    def _maybe_keepalive(self) -> None:
        if not self.on_keepalive:
            return
        now = time.monotonic()
        if now - self._last_keepalive >= KEEPALIVE_INTERVAL:
            log.info("Sending scheduled keepalive")
            self.on_keepalive()
            self._last_keepalive = now

    def _run(self) -> None:
        was_connected = True
        self._last_keepalive = time.monotonic()  # don't fire immediately after login
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
                self._last_keepalive = time.monotonic()  # reset timer after reconnect
                self.on_reconnected()
            else:
                self._maybe_keepalive()
            self._stop_event.wait(POLL_INTERVAL)
