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
