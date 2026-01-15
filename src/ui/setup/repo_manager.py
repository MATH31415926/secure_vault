"""
Secure Vault - Repository Manager Dialog
Repository creation, selection, and management.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QSpinBox, QComboBox,
    QAbstractItemView, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.config import get_config
from src.core.i18n import _
from src.database.database import get_global_database, RepositoryDatabase
from src.repository.repository import (
    list_repositories, create_repository, delete_repository,
    get_disk_total_space, get_repository_stats, set_active_repository,
    import_repository, rename_repository, get_repository, save_repository_config
)
from src.core.hash_utils import format_size
from src.database.models import Repository


class RepositoryManagerDialog(QDialog):
    """Dialog for repository management."""
    
    repository_selected = pyqtSignal(int)  # Emits repository ID when selected
    
    def __init__(self, master_key: bytes, parent=None):
        super().__init__(parent)
        self.master_key = master_key
        self.setWindowTitle(_("repo_mgr_title"))
        self.setMinimumSize(700, 500)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()
        self._load_repositories()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel(_("repo_mgr_main_title"))
        title.setProperty("class", "title")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        subtitle = QLabel(_("repo_mgr_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Repository table
        self.repo_table = QTableWidget()
        self.repo_table.setColumnCount(4)
        self.repo_table.setHorizontalHeaderLabels([
            _("repo_col_name"), _("repo_col_path"), _("repo_col_used"), _("repo_col_limit")
        ])
        self.repo_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.repo_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.repo_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.repo_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.repo_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.repo_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.repo_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.create_btn = QPushButton(_("btn_create_repo"))
        self.create_btn.clicked.connect(self._show_create_dialog)
        action_layout.addWidget(self.create_btn)
        
        self.import_btn = QPushButton(_("btn_import_repo"))
        self.import_btn.clicked.connect(self._import_repository)
        action_layout.addWidget(self.import_btn)
        
        self.delete_btn = QPushButton(_("btn_delete_repo"))
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_repository)
        action_layout.addWidget(self.delete_btn)
        
        action_layout.addStretch()
        
        self.enter_btn = QPushButton(_("btn_enter_repo"))
        self.enter_btn.setProperty("class", "primary")
        self.enter_btn.setEnabled(False)
        self.enter_btn.clicked.connect(self._on_enter)
        action_layout.addWidget(self.enter_btn)
        
        layout.addLayout(action_layout)
    
    def _load_repositories(self):
        """Load repositories into the table."""
        self.repo_table.setRowCount(0)
        repos = list_repositories()
        
        for repo in repos:
            try:
                # Try to load stats (will fail if drive missing)
                stats = get_repository_stats(repo)
                used_text = format_size(stats["used"])
            except Exception:
                # If path invalid or inaccessible, show 0
                used_text = format_size(0)
            
            row = self.repo_table.rowCount()
            self.repo_table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(repo.name)
            name_item.setData(Qt.ItemDataRole.UserRole, repo.id)
            self.repo_table.setItem(row, 0, name_item)
            
            # Path
            self.repo_table.setItem(row, 1, QTableWidgetItem(repo.path))
            
            # Used capacity
            self.repo_table.setItem(row, 2, QTableWidgetItem(used_text))
            
            # Max capacity
            max_text = format_size(repo.max_capacity)
            self.repo_table.setItem(row, 3, QTableWidgetItem(max_text))
        
        self._on_selection_changed()
    
    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.repo_table.selectedItems()) > 0
        self.delete_btn.setEnabled(has_selection)
        self.enter_btn.setEnabled(has_selection)
    
    def _show_create_dialog(self):
        """Show create repository dialog."""
        dialog = CreateRepositoryDialog(self.master_key, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_repositories()
    
    def _delete_repository(self):
        """Delete selected repository and all its data."""
        selected = self.repo_table.selectedItems()
        if not selected:
            return
        
        repo_id = selected[0].data(Qt.ItemDataRole.UserRole)
        repo_name = selected[0].text()
        
        reply = QMessageBox.warning(
            self,
            _("dialog_delete_repo_title"),
            _("dialog_delete_repo_msg", name=repo_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            delete_repository(repo_id, delete_files=True)
            self._load_repositories()
    
    def _import_repository(self):
        """Import a repository from its config file."""
        config_path, _filter = QFileDialog.getOpenFileName(
            self,
            _("dialog_import_repo_title"),
            "",
            _("dialog_import_repo_filter")
        )
        
        if not config_path:
            return
        
        try:
            repo, was_renamed, _err = import_repository(config_path, self.master_key)
            
            if was_renamed:
                QMessageBox.information(
                    self,
                    _("btn_confirm"),
                    _("msg_import_success_renamed", name=repo.name)
                )
            else:
                QMessageBox.information(
                    self,
                    _("btn_confirm"),
                    _("msg_import_success", name=repo.name)
                )
            
            self._load_repositories()
            
        except ValueError as e:
            QMessageBox.warning(
                self,
                _("msg_import_failed"),
                str(e)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                _("msg_import_failed"),
                _("msg_import_error", error=str(e))
            )
    
    def _on_item_double_clicked(self, item):
        """Handle item double-click - rename on name, change capacity, or enter."""
        if item.column() == 0:
            # Name column - allow rename
            self._rename_repository(item)
        elif item.column() == 3:
            # Capacity column - allow change
            self._change_capacity(item)
        else:
            # Other columns - enter repository
            self._on_enter()
    
    def _rename_repository(self, item):
        """Rename a repository."""
        repo_id = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.text()
        
        new_name, ok = QInputDialog.getText(
            self,
            _("dialog_rename_repo_title"),
            _("dialog_rename_repo_msg"),
            text=current_name
        )
        
        if not ok or new_name == current_name:
            return
        
        success, error = rename_repository(repo_id, new_name)
        
        if success:
            self._load_repositories()
        else:
            QMessageBox.warning(
                self,
                _("msg_rename_failed"),
                error
            )
    
    def _change_capacity(self, item):
        """Change repository capacity."""
        # Get repo ID from the first column of the same row
        row = item.row()
        name_item = self.repo_table.item(row, 0)
        repo_id = name_item.data(Qt.ItemDataRole.UserRole)
        
        repo = get_repository(repo_id)
        if repo is None:
            return
        
        # Current capacity in GB
        current_gb = repo.max_capacity / (1024 * 1024 * 1024)
        
        new_gb, ok = QInputDialog.getDouble(
            self,
            _("dialog_capacity_title"),
            _("dialog_capacity_msg"),
            value=current_gb,
            min=0.1,
            max=999999,
            decimals=2
        )
        
        if not ok or new_gb == current_gb:
            return
        
        new_capacity = int(new_gb * 1024 * 1024 * 1024)
        
        # Update in global database
        db = get_global_database()
        db.execute(
            "UPDATE repositories SET max_capacity = ? WHERE id = ?",
            (new_capacity, repo_id)
        )
        db._connection.commit()
        
        # Update config file
        repo.max_capacity = new_capacity
        save_repository_config(repo)
        
        self._load_repositories()
    
    def _on_enter(self):
        """Enter selected repository with validation."""
        selected = self.repo_table.selectedItems()
        if not selected:
            return
        
        repo_id = selected[0].data(Qt.ItemDataRole.UserRole)
        
        # Get fresh repository data
        repo = get_repository(repo_id)
        if repo is None:
            QMessageBox.warning(
                self,
                _("error_repo_not_found"),
                _("error_repo_not_found")
            )
            self._load_repositories()
            return
        
        # Check if repository path exists
        vault_dir = Path(repo.path) / RepositoryDatabase.VAULT_DIR
        if not vault_dir.exists():
            QMessageBox.warning(
                self,
                _("msg_import_failed"),
                _("error_repo_path_not_found", path=repo.path)
            )
            return
        
        try:
            set_active_repository(repo_id)
            self.repository_selected.emit(repo_id)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                _("error_repo_connect", error=""),
                _("error_repo_connect", error=str(e))
            )
            return


class CreateRepositoryDialog(QDialog):
    """Dialog for creating a new repository."""
    
    def __init__(self, master_key: bytes, parent=None):
        super().__init__(parent)
        self.master_key = master_key
        self.setWindowTitle(_("btn_create_repo"))
        self.setFixedSize(500, 350)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)  # Reduce default spacing
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Name
        name_label = QLabel(_("repo_col_name") + ":")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(_("placeholder_repo_name"))
        layout.addWidget(self.name_input)
        
        # Path - add section spacing
        layout.addSpacing(16)
        path_label = QLabel(_("repo_col_path") + ":")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(_("placeholder_select_path"))
        self.path_input.textChanged.connect(self._on_path_changed)
        path_layout.addWidget(self.path_input, 1)
        
        browse_btn = QPushButton(_("btn_browse"))
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Disk info - smaller spacing as it belongs to path section
        self.disk_info = QLabel("")
        self.disk_info.setProperty("class", "subtitle")
        self.disk_info.setContentsMargins(0, 2, 0, 0)
        layout.addWidget(self.disk_info)
        
        # Capacity - add section spacing
        layout.addSpacing(16)
        capacity_label = QLabel(_("repo_col_limit") + ":")
        layout.addWidget(capacity_label)
        
        capacity_layout = QHBoxLayout()
        capacity_layout.setSpacing(8)
        self.capacity_input = QSpinBox()
        self.capacity_input.setRange(1, 999999)
        self.capacity_input.setValue(10)
        self.capacity_input.setFixedWidth(100)
        capacity_layout.addWidget(self.capacity_input)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["GB", "MB", "TB"])
        self.unit_combo.setFixedWidth(80)
        capacity_layout.addWidget(self.unit_combo)
        capacity_layout.addStretch()
        layout.addLayout(capacity_layout)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f14c4c;")
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(_("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton(_("btn_create"))
        self.create_btn.setProperty("class", "primary")
        self.create_btn.clicked.connect(self._create_repository)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_path(self):
        """Open folder browser."""
        path = QFileDialog.getExistingDirectory(
            self,
            _("placeholder_select_path"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.path_input.setText(path)
    
    def _on_path_changed(self):
        """Update disk info when path changes."""
        path = self.path_input.text()
        if not path or not Path(path).exists():
            self.disk_info.setText("")
            return
        
        total = get_disk_total_space(path)
        self.disk_info.setText(_("disk_info", total=format_size(total)))
    
    def _get_capacity_bytes(self) -> int:
        """Get capacity in bytes."""
        value = self.capacity_input.value()
        unit = self.unit_combo.currentText()
        
        multipliers = {
            "MB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
            "TB": 1024 * 1024 * 1024 * 1024,
        }
        
        return value * multipliers[unit]
    
    def _create_repository(self):
        """Create the repository."""
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        capacity = self._get_capacity_bytes()
        
        self.error_label.setText("")
        
        # Validate
        if not name:
            self.error_label.setText(_("error_repo_name_required"))
            return
        
        # Check for duplicate name
        existing_repos = list_repositories()
        for repo in existing_repos:
            if repo.name.lower() == name.lower():
                self.error_label.setText(_("error_repo_name_exists"))
                return
        
        if not path:
            self.error_label.setText(_("error_repo_path_required"))
            return
        
        # Normalize path for comparison
        normalized_path = str(Path(path).resolve())
        
        # Check for duplicate path
        existing_repos = list_repositories()
        for repo in existing_repos:
            if str(Path(repo.path).resolve()) == normalized_path:
                self.error_label.setText(_("error_repo_path_exists"))
                return
        
        # Check disk capacity
        disk_total = get_disk_total_space(path if Path(path).exists() else str(Path(path).parent))
        if capacity > disk_total:
            self.error_label.setText(
                _("error_capacity_too_small", size=format_size(capacity), total=format_size(disk_total))
            )
            return
        
        try:
            create_repository(name, path, capacity, self.master_key)
            self.accept()
        except Exception as e:
            self.error_label.setText(str(e))
