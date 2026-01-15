"""
Secure Vault - Key Setup Dialog
Master key generation (manual or random).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QTextEdit,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.crypto import generate_master_key
from src.core.i18n import _


class KeySetupDialog(QDialog):
    """Dialog for master key generation."""
    
    key_configured = pyqtSignal(bytes)  # Emits the master key when configured
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("key_setup_title"))
        self.setFixedSize(500, 450)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._generated_key: bytes = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Title
        title = QLabel(_("key_setup_main_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(_("key_setup_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Mode selection
        mode_group = QButtonGroup(self)
        
        self.random_radio = QRadioButton(_("radio_random_key"))
        self.random_radio.setChecked(True)
        mode_group.addButton(self.random_radio)
        layout.addWidget(self.random_radio)
        
        self.manual_radio = QRadioButton(_("radio_manual_key"))
        mode_group.addButton(self.manual_radio)
        layout.addWidget(self.manual_radio)
        
        self.random_radio.toggled.connect(self._on_mode_changed)
        
        # Random key display
        self.random_frame = QFrame()
        self.random_frame.setProperty("class", "card")
        random_layout = QVBoxLayout(self.random_frame)
        
        random_label = QLabel(_("label_random_key"))
        random_layout.addWidget(random_label)
        
        self.key_display = QTextEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setMaximumHeight(60)
        self.key_display.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace;"
        )
        random_layout.addWidget(self.key_display)
        
        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton(_("btn_regenerate"))
        self.generate_btn.clicked.connect(self._generate_key)
        btn_row.addWidget(self.generate_btn)
        
        self.copy_btn = QPushButton(_("btn_copy_key"))
        self.copy_btn.clicked.connect(self._copy_key)
        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch()
        random_layout.addLayout(btn_row)
        
        layout.addWidget(self.random_frame)
        
        # Manual key input
        self.manual_frame = QFrame()
        self.manual_frame.setProperty("class", "card")
        self.manual_frame.setVisible(False)
        manual_layout = QVBoxLayout(self.manual_frame)
        
        manual_label = QLabel(_("label_manual_key"))
        manual_layout.addWidget(manual_label)
        
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText(_("placeholder_hex_64"))
        self.manual_input.textChanged.connect(self._validate_manual_key)
        manual_layout.addWidget(self.manual_input)
        
        self.manual_error = QLabel("")
        self.manual_error.setStyleSheet("color: #f14c4c;")
        manual_layout.addWidget(self.manual_error)
        
        layout.addWidget(self.manual_frame)
        
        # Warning
        warning = QLabel(_("label_backup_warning"))
        warning.setStyleSheet("color: #dcdcaa;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.confirm_btn = QPushButton(_("btn_confirm"))
        self.confirm_btn.setProperty("class", "primary")
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Generate initial key
        self._generate_key()
    
    def _on_mode_changed(self, is_random: bool):
        """Handle mode toggle."""
        self.random_frame.setVisible(is_random)
        self.manual_frame.setVisible(not is_random)
        self._validate_confirm_button()
    
    def _generate_key(self):
        """Generate a new random key."""
        self._generated_key = generate_master_key()
        self.key_display.setText(self._generated_key.hex())
        self._validate_confirm_button()
    
    def _copy_key(self):
        """Copy key to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._generated_key.hex())
        
        # Show feedback
        QMessageBox.information(
            self,
            _("msg_key_copied_title"),
            _("msg_key_copied_msg")
        )
    
    def _validate_manual_key(self):
        """Validate manual key input."""
        text = self.manual_input.text().strip()
        self.manual_error.setText("")
        
        if not text:
            return
        
        # Check length
        if len(text) != 64:
            self.manual_error.setText(_("error_hex_length", count=len(text)))
            return
        
        # Check hex
        try:
            bytes.fromhex(text)
        except ValueError:
            self.manual_error.setText(_("error_hex_invalid"))
            return
        
        self._validate_confirm_button()
    
    def _validate_confirm_button(self):
        """Update confirm button state."""
        if self.random_radio.isChecked():
            self.confirm_btn.setEnabled(self._generated_key is not None)
        else:
            text = self.manual_input.text().strip()
            try:
                is_valid = len(text) == 64 and bytes.fromhex(text)
                self.confirm_btn.setEnabled(is_valid)
            except ValueError:
                self.confirm_btn.setEnabled(False)
    
    def _on_confirm(self):
        """Handle confirm button click."""
        if self.random_radio.isChecked():
            key = self._generated_key
        else:
            key = bytes.fromhex(self.manual_input.text().strip())
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            _("dialog_confirm_key_title"),
            _("dialog_confirm_key_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.key_configured.emit(key)
            self.accept()
