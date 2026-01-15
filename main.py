"""
Secure Vault - Application Entry Point
Bootstrap and application flow management.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from src.core.config import get_config
from src.core.crypto import (
    encrypt_master_key, decrypt_master_key, compute_key_hash, verify_key_hash,
    CryptoError
)
from src.database.database import get_database, close_database
from src.repository.repository import get_active_repository
from src.ui.styles import get_stylesheet
from src.ui.window_utils import patch_qt_dialogs
from src.ui.setup.pin_setup import PinSetupDialog, PinVerifyDialog
from src.ui.setup.key_setup import KeySetupDialog
from src.ui.setup.repo_manager import RepositoryManagerDialog
from src.ui.main.main_window import MainWindow
from src.utils.logger import get_logger


class SecureVaultApp:
    """Main application controller."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Secure Vault")
        self.app.setApplicationVersion("1.0.0")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        self.config = get_config()
        self.master_key: bytes = None
        self.main_window: MainWindow = None
        
        # Apply initial theme
        self.app.setStyleSheet(get_stylesheet(self.config.dark_mode))
        patch_qt_dialogs()  # Enable global theme sync for dialogs
        
        # Initialize database
        get_database()
        
        # Initialize logger
        self.logger = get_logger()
    
    def run(self) -> int:
        """Run the application."""
        try:
            if self.config.is_first_run:
                # First time setup
                if not self._first_time_setup():
                    return 0
            else:
                # Returning user - verify PIN
                if not self._verify_pin():
                    return 0
            
            # Repository selection
            if not self._select_repository():
                return 0
            
            # Get active repository
            repo = get_active_repository()
            if not repo:
                QMessageBox.critical(
                    None,
                    "错误",
                    "未找到有效的仓库。"
                )
                return 1
            
            # Show main window
            self.main_window = MainWindow(self.master_key, repo)
            self.main_window.show()
            
            return self.app.exec()
            
        except Exception as e:
            QMessageBox.critical(
                None,
                "错误",
                f"应用程序错误:\n{str(e)}"
            )
            return 1
        finally:
            close_database()
    
    def _first_time_setup(self) -> bool:
        """Handle first-time setup flow."""
        self.logger.info("首次运行 - 开始设置向导")
        
        # Step 1: PIN setup
        pin_dialog = PinSetupDialog()
        pin: str = None
        
        def on_pin_configured(p):
            nonlocal pin
            pin = p
        
        pin_dialog.pin_configured.connect(on_pin_configured)
        
        if pin_dialog.exec() != PinSetupDialog.DialogCode.Accepted:
            return False
        
        if not pin:
            return False
        
        # Step 2: Key generation
        key_dialog = KeySetupDialog()
        master_key: bytes = None
        
        def on_key_configured(k):
            nonlocal master_key
            master_key = k
        
        key_dialog.key_configured.connect(on_key_configured)
        
        if key_dialog.exec() != KeySetupDialog.DialogCode.Accepted:
            return False
        
        if not master_key:
            return False
        
        # Encrypt and save master key
        encrypted_key, salt, nonce = encrypt_master_key(master_key, pin)
        key_hash = compute_key_hash(master_key)
        
        self.config.encrypted_master_key = encrypted_key
        self.config.master_key_salt = salt
        self.config.master_key_nonce = nonce
        self.config.master_key_hash = key_hash
        
        self.master_key = master_key
        self.logger.info("PIN 和密钥已配置")
        
        return True
    
    def _verify_pin(self) -> bool:
        """Verify PIN and decrypt master key."""
        pin_dialog = PinVerifyDialog()
        verified = False
        
        def on_pin_verified(pin: str):
            nonlocal verified
            try:
                # Attempt to decrypt master key
                decrypted_key = decrypt_master_key(
                    self.config.encrypted_master_key,
                    pin,
                    self.config.master_key_salt,
                    self.config.master_key_nonce
                )
                
                # Verify hash
                if verify_key_hash(decrypted_key, self.config.master_key_hash):
                    self.master_key = decrypted_key
                    verified = True
                    pin_dialog.accept()
                    self.logger.info("PIN 码验证成功")
                else:
                    pin_dialog.show_error("PIN 码错误")
                    self.logger.warning("PIN 验证失败 - 哈希不匹配")
            except CryptoError:
                pin_dialog.show_error("PIN 码错误")
                self.logger.warning("PIN 验证失败 - 解密错误")
        
        pin_dialog.pin_verified.connect(on_pin_verified)
        
        if pin_dialog.exec() != PinVerifyDialog.DialogCode.Accepted:
            return False
        
        return verified
    
    def _select_repository(self) -> bool:
        """Show repository selection dialog."""
        # Check if we have an active repository that still exists
        active_repo = get_active_repository()
        if active_repo:
            return True
        
        # Show repository manager
        repo_dialog = RepositoryManagerDialog(self.master_key)
        selected = False
        
        def on_repo_selected(repo_id: int):
            nonlocal selected
            selected = True
            self.logger.info(f"已选择仓库 ID: {repo_id}")
        
        repo_dialog.repository_selected.connect(on_repo_selected)
        
        if repo_dialog.exec() != RepositoryManagerDialog.DialogCode.Accepted:
            return False
        
        return selected


def main():
    """Application entry point."""
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # Run the application
    app_instance = SecureVaultApp()
    exit_code = app_instance.run()
    
    # Explicitly delete instance to ensure proper cleanup order
    # (Fixes QThreadStorage: entry destroyed before end of thread)
    del app_instance
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
