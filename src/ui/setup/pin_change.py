"""
Secure Vault - PIN Change Dialog
Change PIN after verifying current PIN.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.config import get_config
from src.core.crypto import (
    decrypt_master_key, encrypt_master_key, verify_key_hash, CryptoError
)
from src.core.i18n import _


class PinChangeDialog(QDialog):
    """Dialog for changing PIN code."""
    
    pin_changed = pyqtSignal()  # Emitted when PIN is successfully changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("pin_change_title"))
        self.setFixedSize(420, 380)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._master_key: bytes = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel(_("pin_change_title"))
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(24)
        
        # Current PIN
        current_label = QLabel(_("label_current_pin"))
        layout.addWidget(current_label)
        
        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_input.setPlaceholderText(_("placeholder_current_pin"))
        layout.addWidget(self.current_input)
        
        layout.addSpacing(16)
        
        # New PIN
        new_label = QLabel(_("label_new_pin"))
        layout.addWidget(new_label)
        
        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_input.setPlaceholderText(_("placeholder_new_pin"))
        layout.addWidget(self.new_input)
        
        layout.addSpacing(16)
        
        # Confirm new PIN
        confirm_label = QLabel(_("label_confirm_new_pin"))
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText(_("placeholder_confirm_new_pin"))
        layout.addWidget(self.confirm_input)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f14c4c;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(_("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.change_btn = QPushButton(_("btn_change"))
        self.change_btn.setProperty("class", "primary")
        self.change_btn.clicked.connect(self._on_change)
        btn_layout.addWidget(self.change_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_change(self):
        """Handle change button click."""
        current_pin = self.current_input.text()
        new_pin = self.new_input.text()
        confirm_pin = self.confirm_input.text()
        
        self.error_label.setText("")
        
        # Validate inputs
        if not current_pin:
            self.error_label.setText(_("error_current_pin_required"))
            return
        
        if len(new_pin) < 4:
            self.error_label.setText(_("error_new_pin_min_length"))
            return
        
        if new_pin != confirm_pin:
            self.error_label.setText(_("error_new_pin_mismatch"))
            return
        
        if current_pin == new_pin:
            self.error_label.setText(_("error_new_pin_same_as_current"))
            return
        
        # Verify current PIN
        config = get_config()
        try:
            decrypted_key = decrypt_master_key(
                config.encrypted_master_key,
                current_pin,
                config.master_key_salt,
                config.master_key_nonce
            )
            
            if not verify_key_hash(decrypted_key, config.master_key_hash):
                self.error_label.setText(_("error_pin_invalid"))
                return
            
            self._master_key = decrypted_key
            
        except CryptoError:
            self.error_label.setText(_("error_pin_invalid"))
            return
        
        # Encrypt master key with new PIN
        encrypted_key, salt, nonce = encrypt_master_key(self._master_key, new_pin)
        
        # Save new encrypted key
        config.encrypted_master_key = encrypted_key
        config.master_key_salt = salt
        config.master_key_nonce = nonce
        
        # Show success message
        QMessageBox.information(
            self,
            _("label_success"),
            _("msg_pin_change_success")
        )
        
        self.pin_changed.emit()
        self.accept()
