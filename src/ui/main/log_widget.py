"""
Secure Vault - Log Widget
Real-time log display with color coding.
"""

from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QTextCharFormat, QColor, QFont

from src.ui.styles import get_log_colors
from src.core.i18n import _


class LogWidget(QPlainTextEdit):
    """Widget for displaying operation logs."""
    
    def __init__(self, dark_mode: bool = True, parent=None):
        super().__init__(parent)
        self._dark_mode = dark_mode
        self._setup_ui()
    
    def contextMenuEvent(self, event):
        """Show context menu on right click."""
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        
        clear_action = menu.addAction(_("log_clear"))
        clear_action.triggered.connect(self.clear_logs)
        
        menu.exec(event.globalPos())
    
    def _setup_ui(self):
        """Setup widget appearance."""
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)  # Limit lines
        
        # Font
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Size
        self.setMinimumHeight(100)
        self.setMaximumHeight(200)
    
    def set_dark_mode(self, dark_mode: bool):
        """Update dark mode setting."""
        self._dark_mode = dark_mode
    
    @pyqtSlot(str, str, str)
    def add_log(self, timestamp: str, level: str, message: str):
        """
        Add a log entry.
        
        Args:
            timestamp: Time string (HH:MM:SS)
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
        """
        colors = get_log_colors(self._dark_mode)
        color = colors.get(level, colors["INFO"])
        
        # Format line
        line = f"[{timestamp}] [{level}] {message}"
        
        # Use appendPlainText which is thread-safe and doesn't cause cursor issues
        self.appendPlainText(line)
        
        # Apply color to last block
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.KeepAnchor)
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.mergeCharFormat(fmt)
    
    def add_info(self, message: str):
        """Add an info log entry."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.add_log(timestamp, "INFO", message)
    
    def add_warning(self, message: str):
        """Add a warning log entry."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.add_log(timestamp, "WARNING", message)
    
    def add_error(self, message: str):
        """Add an error log entry."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.add_log(timestamp, "ERROR", message)
    
    def clear_logs(self):
        """Clear all log entries."""
        self.clear()
