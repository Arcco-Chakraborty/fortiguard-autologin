import logging
import pystray
from PIL import Image, ImageDraw
from startup import enable_startup, disable_startup, is_startup_enabled
from setup_ui import show_setup_window

log = logging.getLogger(__name__)


def _make_icon(color: str) -> Image.Image:
    """Create a solid colored circle icon that's visible on any taskbar theme."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Solid circle with a thin dark border for visibility on light backgrounds
    draw.ellipse([4, 4, 60, 60], fill=color, outline="#333333", width=2)
    return img


ICON_CONNECTED = _make_icon("#22c55e")
ICON_RECONNECTING = _make_icon("#eab308")


def create_tray(on_quit, on_ready=None) -> pystray.Icon:
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

    def _setup(icon):
        icon.visible = True
        log.info("Tray icon is now visible")
        if on_ready:
            on_ready(icon)

    icon._setup_func = _setup
    return icon


def run_tray(icon: pystray.Icon) -> None:
    """Start the tray icon event loop (blocks until quit)."""
    log.info("Starting tray event loop")
    icon.run(setup=icon._setup_func)


def set_connected(icon: pystray.Icon) -> None:
    icon._state["connected"] = True
    icon.icon = ICON_CONNECTED
    icon.title = "FortiGuard Auto-Login — Connected"
    log.info("Status: Connected")


def set_reconnecting(icon: pystray.Icon) -> None:
    icon._state["connected"] = False
    icon.icon = ICON_RECONNECTING
    icon.title = "FortiGuard Auto-Login — Reconnecting..."
    log.info("Status: Reconnecting")
