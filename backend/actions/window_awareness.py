import pygetwindow as gw

def get_active_window_info() -> str:
    """Returns the title and application name of the currently focused window."""
    try:
        window = gw.getActiveWindow()
        if window:
            return f"Currently active window: '{window.title}'"
        return "No active window detected."
    except Exception:
        return "Could not determine active window."
