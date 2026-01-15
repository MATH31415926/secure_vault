import sys
import ctypes
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, QEvent

def apply_native_theme(window: QWidget, dark_mode: bool):
    """
    Apply native Windows theme to the window title bar.
    Only supports Windows 10 (1809+) and Windows 11.
    """
    if sys.platform != "win32":
        return

    from PyQt6.QtCore import QTimer
    
    def _do_apply():
        try:
            if not window.isVisible() and not window.isWindow():
                return
            
            hwnd = int(window.winId())
            if not hwnd:
                return
                
            win_version = sys.getwindowsversion()
            if win_version.major == 10 and win_version.build >= 17763:
                attribute = 20 if win_version.build >= 18985 else 19
                value = ctypes.c_int(1 if dark_mode else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 
                    attribute, 
                    ctypes.byref(value), 
                    ctypes.sizeof(value)
                )
        except Exception:
            pass
            
    # Apply immediately
    _do_apply()
    # Also apply after a small delay to ensure it "sticks" as OS mappings settle
    QTimer.singleShot(50, _do_apply)

class NativeThemeEventFilter(QObject):
    """
    Global event filter to apply native theme to all windows as they are shown.
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            if isinstance(obj, QWidget) and obj.isWindow():
                from src.core.config import get_config
                config = get_config()
                apply_native_theme(obj, config.dark_mode)
        return super().eventFilter(obj, event)

# Global filter instance to prevent garbage collection
_global_filter = None

def install_theme_filter(app):
    """
    Install the global theme event filter on the application.
    """
    global _global_filter
    if _global_filter is None:
        _global_filter = NativeThemeEventFilter()
        app.installEventFilter(_global_filter)
    
    # Also apply to all existing windows
    from src.core.config import get_config
    update_all_windows_theme(get_config().dark_mode)

def update_all_windows_theme(dark_mode: bool):
    """
    Force update the native theme of all top-level windows.
    """
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        return
        
    for widget in app.topLevelWidgets():
        if widget.isWindow():
            apply_native_theme(widget, dark_mode)

def patch_qt_dialogs():
    """Compatibility wrapper for previously used function name."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        install_theme_filter(app)
