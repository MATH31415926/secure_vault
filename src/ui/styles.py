"""
Secure Vault - UI Styles
Dark and light theme stylesheets for Windows Explorer-like appearance.
"""

# Color palette - Dark theme
DARK_COLORS = {
    "bg_primary": "#1e1e1e",
    "bg_secondary": "#252526",
    "bg_tertiary": "#2d2d30",
    "bg_hover": "#3e3e42",
    "bg_selected": "#094771",
    "border": "#3f3f46",
    "text_primary": "#ffffff",
    "text_secondary": "#cccccc",
    "text_muted": "#858585",
    "accent": "#0078d4",
    "accent_hover": "#1e8ad4",
    "success": "#4ec9b0",
    "warning": "#dcdcaa",
    "error": "#f14c4c",
    "scrollbar": "#4a4a4a",
    "scrollbar_hover": "#5a5a5a",
}

# Color palette - Light theme
LIGHT_COLORS = {
    "bg_primary": "#ffffff",
    "bg_secondary": "#f3f3f3",
    "bg_tertiary": "#e5e5e5",
    "bg_hover": "#e8e8e8",
    "bg_selected": "#cce8ff",
    "border": "#d4d4d4",
    "text_primary": "#1e1e1e",
    "text_secondary": "#444444",
    "text_muted": "#777777",
    "accent": "#0078d4",
    "accent_hover": "#106ebe",
    "success": "#16825d",
    "warning": "#bf8803",
    "error": "#f14c4c",
    "scrollbar": "#c1c1c1",
    "scrollbar_hover": "#a8a8a8",
}


def get_stylesheet(dark_mode: bool = True) -> str:
    """
    Get the complete stylesheet for the application.
    
    Args:
        dark_mode: If True, return dark theme; otherwise light theme
    
    Returns:
        QSS stylesheet string
    """
    c = DARK_COLORS if dark_mode else LIGHT_COLORS
    
    return f"""
    /* Global styles */
    QWidget {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
        font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
        font-size: 13px;
    }}
    
    /* Main window */
    QMainWindow {{
        background-color: {c["bg_primary"]};
    }}
    
    /* Dialog */
    QDialog {{
        background-color: {c["bg_primary"]};
    }}
    
    /* Labels */
    QLabel {{
        color: {c["text_primary"]};
        background: transparent;
    }}
    
    QLabel[class="title"] {{
        font-size: 20px;
        font-weight: bold;
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 14px;
        color: {c["text_secondary"]};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 80px;
        min-height: 18px;
    }}
    
    QPushButton:hover {{
        background-color: {c["bg_hover"]};
        border-color: {c["accent"]};
    }}
    
    QPushButton:pressed {{
        background-color: {c["accent"]};
    }}
    
    QPushButton:disabled {{
        color: {c["text_muted"]};
        background-color: {c["bg_secondary"]};
    }}
    
    QPushButton[class="primary"] {{
        background-color: {c["accent"]};
        border-color: {c["accent"]};
        color: white;
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {c["accent_hover"]};
    }}
    
    QPushButton[class="danger"] {{
        background-color: {c["error"]};
        border-color: {c["error"]};
        color: white;
    }}
    
    QPushButton[class="icon"] {{
        background: transparent;
        border: none;
        padding: 4px;
        min-width: 32px;
        min-height: 32px;
        border-radius: 4px;
    }}
    
    QPushButton[class="icon"]:hover {{
        background-color: {c["bg_hover"]};
    }}
    
    /* Line Edit */
    QLineEdit {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 10px 14px;
        font-size: 14px;
        min-height: 17px;
        selection-background-color: {c["accent"]};
    }}
    
    QLineEdit::placeholder {{
        color: {c["text_muted"]};
    }}
    
    QLineEdit:focus {{
        border-color: {c["accent"]};
        background-color: {c["bg_secondary"]};
    }}
    
    QLineEdit:disabled {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_muted"]};
    }}
    
    /* Spin Box */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 4px 8px;
        min-height: 18px;
    }}
    
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        width: 20px;
        border: none;
        background: transparent;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c["accent"]};
    }}
    
    /* Combo Box */
    QComboBox {{
        background-color: {c["bg_tertiary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 4px 12px;
        min-width: 80px;
        min-height: 18px;
    }}

    QComboBox:hover {{
        border-color: {c["accent"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 0px;
        height: 0px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: none;
        border: none;
        background: transparent;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["bg_selected"]};
    }}

    /* Title bar combo box (transparent background) */
    QComboBox[class="titlebar"] {{
        background-color: transparent;
        border: 1px solid transparent;
        padding: 4px 8px;
    }}

    QComboBox[class="titlebar"]:hover {{
        background-color: {c["bg_hover"]};
        border-color: transparent;
    }}

    QComboBox[class="titlebar"]::drop-down {{
        width: 0px;
        height: 0px;
        border: none;
        background: transparent;
    }}

    QComboBox[class="titlebar"]::down-arrow {{
        image: none;
        width: 0px;
        height: 0px;
        border: none;
        background: transparent;
    }}

    QComboBox[class="titlebar"] QAbstractItemView {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["bg_selected"]};
        outline: none;
    }}

    QComboBox[class="titlebar"] QAbstractItemView::item {{
        padding: 6px 12px;
        border: none;
    }}

    QComboBox[class="titlebar"] QAbstractItemView::item:selected {{
        background-color: {c["bg_selected"]};
        color: {c["text_primary"]};
    }}

    
    /* Tree View (File Explorer style) */
    QTreeView {{
        background-color: {c["bg_primary"]};
        alternate-background-color: {c["bg_secondary"]};
        border: none;
        border-top: 1px solid {c["border"]};
        border-radius: 0px;
        outline: none;
    }}
    
    QTreeView::item {{
        padding: 4px 8px;
        border: none;
    }}
    
    QTreeView::item:hover {{
        background-color: {c["bg_hover"]};
    }}
    
    QTreeView::item:selected {{
        background-color: {c["bg_selected"]};
    }}
    
    QTreeView::branch {{
        background: transparent;
    }}
    
    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {{
        border-image: none;
    }}
    
    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children:has-siblings {{
        border-image: none;
    }}
    
    /* Header View */
    QHeaderView {{
        background-color: {c["bg_secondary"]};
        border: none;
    }}
    
    QHeaderView::section {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        padding: 8px 12px;
        border: none;
        border-right: 1px solid {c["border"]};
        border-bottom: 1px solid {c["border"]};
    }}
    
    QHeaderView::section:hover {{
        background-color: {c["bg_hover"]};
    }}
    
    QHeaderView::section:pressed {{
        background-color: {c["bg_tertiary"]};
    }}
    
    /* Table View */
    QTableView {{
        background-color: {c["bg_primary"]};
        border: 1px solid {c["border"]};
        gridline-color: {c["border"]};
    }}
    
    QTableView::item {{
        padding: 6px;
    }}
    
    QTableView::item:selected {{
        background-color: {c["bg_selected"]};
    }}
    
    /* Scroll Bar */
    QScrollBar:vertical {{
        background-color: {c["bg_primary"]};
        width: 12px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {c["scrollbar"]};
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {c["scrollbar_hover"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        background-color: {c["bg_primary"]};
        height: 12px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {c["scrollbar"]};
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {c["scrollbar_hover"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {c["bg_tertiary"]};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: 4px;
    }}
    
    /* Text Edit / Plain Text Edit (Log view) */
    QTextEdit, QPlainTextEdit {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 8px;
        font-family: "Cascadia Code", "Consolas", monospace;
        font-size: 12px;
    }}
    
    /* Menu */
    QMenu {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {c["bg_hover"]};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {c["border"]};
        margin: 4px 8px;
    }}
    
    /* Message Box */
    QMessageBox {{
        background-color: {c["bg_primary"]};
    }}
    
    QMessageBox QLabel {{
        color: {c["text_primary"]};
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: {c["border"]};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    /* Frame */
    QFrame[class="card"] {{
        background-color: {c["bg_secondary"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
    }}
    
    /* Group Box */
    QGroupBox {{
        border: 1px solid {c["border"]};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 8px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
    }}
    
    /* ToolTip */
    QToolTip {{
        background-color: {c["bg_secondary"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """


def get_log_colors(dark_mode: bool = True) -> dict:
    """
    Get colors for log level highlighting.
    
    Returns:
        Dictionary mapping log levels to colors
    """
    c = DARK_COLORS if dark_mode else LIGHT_COLORS
    return {
        "DEBUG": c["text_muted"],
        "INFO": c["text_secondary"],
        "WARNING": c["warning"],
        "ERROR": c["error"],
    }
