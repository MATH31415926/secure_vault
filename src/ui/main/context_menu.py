"""
Secure Vault - Context Menu
Right-click menu for file operations.
"""

from PyQt6.QtWidgets import QMenu, QInputDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction

from src.database.models import VirtualFile
from src.core.i18n import _


class FileContextMenu(QObject):
    """Context menu for file tree operations."""
    
    # Signals for operations
    delete_requested = pyqtSignal(list)  # List of VirtualFile
    rename_requested = pyqtSignal(object, str)  # VirtualFile, new_name
    comment_requested = pyqtSignal(object, str)  # VirtualFile, new_comment
    export_decrypted_requested = pyqtSignal(list, str)  # List of VirtualFile, output_dir
    new_folder_requested = pyqtSignal(object)  # VirtualFile (parent) or None (root)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def show_menu(self, files: list, global_pos):
        """
        Show context menu for selected files.
        
        Args:
            files: List of selected VirtualFile objects
            global_pos: Global position for menu
        """
        from PyQt6.QtWidgets import QApplication
        
        if not files:
            files = []
        
        # Create menu with parent to inherit stylesheet
        parent_widget = QApplication.activeWindow()
        menu = QMenu(parent_widget)
        
        # New Folder Action
        # Logic: 
        # - If no selection -> New Folder in Root
        # - If 1 directory selected -> New Folder inside that directory
        
        single_file = len(files) == 1
        file = files[0] if single_file else None
        
        target_parent = None
        can_create_folder = False
        
        if not files:
            target_parent = None # Root
            can_create_folder = True
        elif single_file and file.is_directory:
            target_parent = file
            can_create_folder = True
            
        if can_create_folder:
            new_folder_action = QAction(_("menu_new_folder"), menu)
            new_folder_action.triggered.connect(
                lambda: self.new_folder_requested.emit(target_parent)
            )
            menu.addAction(new_folder_action)
            menu.addSeparator()
            
        # If no files selected, we only show "New Folder" (and maybe Paste later)
        if not files:
            menu.exec(global_pos)
            return

        # Rename (single file only)
        if single_file:
            rename_action = QAction(_("menu_rename"), menu)
            rename_action.triggered.connect(
                lambda: self._on_rename(file)
            )
            menu.addAction(rename_action)
            
            # Comment
            comment_action = QAction(_("menu_edit_comment"), menu)
            comment_action.triggered.connect(
                lambda: self._on_comment(file)
            )
            menu.addAction(comment_action)
            
            menu.addSeparator()
        
        # Export decrypted
        export_action = QAction(_("menu_export_decrypted"), menu)
        export_action.triggered.connect(
            lambda: self._on_export_decrypted(files)
        )
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction(_("menu_delete"), menu)
        delete_action.triggered.connect(
            lambda: self._on_delete(files)
        )
        menu.addAction(delete_action)
        
        menu.exec(global_pos)
    
    def _on_rename(self, file: VirtualFile):
        """Handle rename action."""
        from PyQt6.QtWidgets import QApplication
        parent = QApplication.activeWindow()
        
        # Get current name (need to decrypt)
        current_name = file.name if file.name else _("label_unknown")
        
        new_name, ok = QInputDialog.getText(
            parent,
            _("dialog_rename_title"),
            _("dialog_rename_msg"),
            text=current_name
        )
        
        if ok and new_name and new_name != current_name:
            self.rename_requested.emit(file, new_name)
    
    def _on_comment(self, file: VirtualFile):
        """Handle comment action."""
        from PyQt6.QtWidgets import QApplication
        parent = QApplication.activeWindow()
        
        current_comment = file.comment if file.comment else ""
        
        new_comment, ok = QInputDialog.getText(
            parent,
            _("dialog_edit_comment_title"),
            _("dialog_edit_comment_msg"),
            text=current_comment
        )
        
        if ok:
            self.comment_requested.emit(file, new_comment)
    
    def _on_delete(self, files: list):
        """Handle delete action."""
        from PyQt6.QtWidgets import QApplication
        parent = QApplication.activeWindow()
        
        count = len(files)
        if count == 1:
            name = files[0].name if files[0].name else _("label_selected_item")
            message = _("dialog_delete_confirm_msg_single", name=name)
        else:
            message = _("dialog_delete_confirm_msg_multiple", count=count)
        
        reply = QMessageBox.question(
            parent,
            _("dialog_delete_confirm_title"),
            message + _("dialog_delete_confirm_suffix"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(files)
    
    def _on_export_decrypted(self, files: list):
        """Handle export decrypted action."""
        from PyQt6.QtWidgets import QApplication
        parent = QApplication.activeWindow()
        
        output_dir = QFileDialog.getExistingDirectory(
            parent,
            _("dialog_export_title"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if output_dir:
            self.export_decrypted_requested.emit(files, output_dir)
