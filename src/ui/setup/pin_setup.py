"""
Secure Vault - PIN Setup Dialog
First-time PIN configuration with confirmation.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.i18n import _


class PinSetupDialog(QDialog):
    """Dialog for first-time PIN setup."""
    
    pin_configured = pyqtSignal(str)  # Emits the PIN when configured
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("pin_setup_title"))
        self.setFixedSize(450, 350)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel(_("setup_pin"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(_("subtitle_pin_protection"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # PIN input
        pin_label = QLabel(_("pin_label"))
        layout.addWidget(pin_label)
        
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText(_("placeholder_enter_pin"))
        self.pin_input.textChanged.connect(self._on_pin_changed)
        layout.addWidget(self.pin_input)
        
        # Confirm PIN input
        confirm_label = QLabel(_("confirm_pin_label"))
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText(_("placeholder_confirm_pin"))
        self.confirm_input.textChanged.connect(self._on_pin_changed)
        layout.addWidget(self.confirm_input)
        
        # Strength indicator
        strength_layout = QHBoxLayout()
        strength_label = QLabel(_("strength_label"))
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(8)
        strength_layout.addWidget(strength_label)
        strength_layout.addWidget(self.strength_bar, 1)
        layout.addLayout(strength_layout)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f14c4c;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.confirm_btn = QPushButton(_("btn_confirm"))
        self.confirm_btn.setProperty("class", "primary")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
    
    def _calculate_strength(self, pin: str) -> int:
        """Calculate PIN strength (0-100)."""
        if not pin:
            return 0
        
        score = 0
        
        # Length score
        if len(pin) >= 4:
            score += 25
        if len(pin) >= 6:
            score += 25
        if len(pin) >= 8:
            score += 15
        
        # Character variety
        has_lower = any(c.islower() for c in pin)
        has_upper = any(c.isupper() for c in pin)
        has_digit = any(c.isdigit() for c in pin)
        has_special = any(not c.isalnum() for c in pin)
        
        variety = sum([has_lower, has_upper, has_digit, has_special])
        score += variety * 10
        
        return min(score, 100)
    
    def _on_pin_changed(self):
        """Handle PIN input changes."""
        pin = self.pin_input.text()
        confirm = self.confirm_input.text()
        
        # Update strength bar
        strength = self._calculate_strength(pin)
        self.strength_bar.setValue(strength)
        
        # Update strength bar color
        if strength < 30:
            self.strength_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #f14c4c; }"
            )
        elif strength < 60:
            self.strength_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #dcdcaa; }"
            )
        else:
            self.strength_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #4ec9b0; }"
            )
        
        # Validate
        self.error_label.setText("")
        valid = True
        
        if len(pin) < 4:
            if pin:
                self.error_label.setText(_("error_pin_min_length"))
            valid = False
        elif pin != confirm:
            if confirm:
                self.error_label.setText(_("error_pin_mismatch"))
            valid = False
        
        self.confirm_btn.setEnabled(valid)
    
    def _on_confirm(self):
        """Handle confirm button click."""
        pin = self.pin_input.text()
        self.pin_configured.emit(pin)
        self.accept()


class PinVerifyDialog(QDialog):
    """Dialog for PIN verification on subsequent launches."""
    
    pin_verified = pyqtSignal(str)  # Emits the PIN when verified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("pin_verify_title"))
        self.setFixedSize(400, 250)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("🔒 Secure Vault")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(_("subtitle_unlock"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText(_("placeholder_enter_pin"))
        self.pin_input.returnPressed.connect(self._on_unlock)
        layout.addWidget(self.pin_input)

        layout.addSpacing(2)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f14c4c;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.unlock_btn = QPushButton(_("btn_unlock"))
        self.unlock_btn.setProperty("class", "primary")
        self.unlock_btn.clicked.connect(self._on_unlock)
        btn_layout.addWidget(self.unlock_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_unlock(self):
        """Handle unlock button click."""
        pin = self.pin_input.text()
        if not pin:
            self.error_label.setText(_("error_pin_required"))
            return
        
        self.pin_verified.emit(pin)
    
    def show_error(self, message: str):
        """Show error message."""
        self.error_label.setText(message)
        self.pin_input.clear()
        self.pin_input.setFocus()
