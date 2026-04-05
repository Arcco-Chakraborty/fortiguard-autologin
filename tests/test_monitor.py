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
