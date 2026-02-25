# lovelace/browser/file_browser.py - File browser panel

import os
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QMenu, QMessageBox, QInputDialog,
    QHBoxLayout, QLabel, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QDir, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QFileSystemModel, QFont

from lovelace.config.settings import Settings


ADA_EXTENSIONS = {
    ".adb", ".ads", ".ali"
}


class AdaFileFilterProxy(QSortFilterProxyModel):
    """Proxy model that optionally hides non-Ada files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = False

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.enabled:
            return True

        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)

        if model.isDir(index):
            return True

        _, ext = os.path.splitext(model.fileName(index))
        return ext.lower() in ADA_EXTENSIONS


class FileBrowser(QWidget):
    """Left-panel file tree widget."""

    file_selected = pyqtSignal(str)   # Emits absolute path of chosen file
    root_path_changed = pyqtSignal(str)
    bookmarks_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self._root_path: Path | None = None
        self._bookmarks: list[Path] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header for Toolbar
        self.header = QWidget()
        self.header.setStyleSheet("background-color: #2D2D2D; padding: 4px;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel("EXPLORER")
        self.title_label.setFont(QFont("Monospace", 9, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #808080;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Navigation buttons
        self.home_btn = QToolButton()
        self.home_btn.setText("⌂")
        self.home_btn.setToolTip("Go to Home Directory")
        self.home_btn.clicked.connect(self._go_home)
        self.home_btn.setStyleSheet("QToolButton { background: transparent; color: #808080; border: none; font-size: 14px; padding: 0 4px; } QToolButton:hover { color: #D4D4D4; }")
        header_layout.addWidget(self.home_btn)

        self.up_btn = QToolButton()
        self.up_btn.setText("↑")
        self.up_btn.setToolTip("Go Up to Parent Folder")
        self.up_btn.clicked.connect(self._go_up)
        self.up_btn.setStyleSheet("QToolButton { background: transparent; color: #808080; border: none; font-size: 14px; padding: 0 4px; } QToolButton:hover { color: #D4D4D4; }")
        header_layout.addWidget(self.up_btn)

        self.bookmarks_btn = QToolButton()
        self.bookmarks_btn.setText("★")
        self.bookmarks_btn.setToolTip("Bookmarks")
        self.bookmarks_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.bookmarks_btn.setStyleSheet("QToolButton { background: transparent; color: #808080; border: none; font-size: 14px; padding: 0 4px; } QToolButton::menu-indicator { image: none; } QToolButton:hover { color: #D4D4D4; }")
        
        self.bookmarks_menu = QMenu(self)
        self.bookmarks_menu.aboutToShow.connect(self._update_bookmarks_menu)
        self.bookmarks_btn.setMenu(self.bookmarks_menu)
        header_layout.addWidget(self.bookmarks_btn)

        layout.addWidget(self.header)

        # Filesystem model
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.rootPath())

        # Filter proxy
        self.proxy_model = AdaFileFilterProxy(self)
        self.proxy_model.setSourceModel(self.fs_model)
        self.proxy_model.enabled = bool(self.settings.get("browser", "ada_filter"))

        # Tree view
        self.tree = QTreeView()
        self.tree.setModel(self.proxy_model)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)

        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.tree)
        self._load_settings()

    def set_root(self, path: str) -> None:
        self._root_path = Path(path)
        src_idx = self.fs_model.index(str(self._root_path))
        proxy_idx = self.proxy_model.mapFromSource(src_idx)
        self.tree.setRootIndex(proxy_idx)
        self.title_label.setText(self._root_path.name.upper())
        self.settings.set("browser", "last_directory", str(self._root_path))
        self.settings.save()
        self.root_path_changed.emit(str(self._root_path))

    def _go_home(self):
        self.set_root(str(Path.home()))

    def _go_up(self):
        if self._root_path and self._root_path.parent != self._root_path:
            self.set_root(str(self._root_path.parent))

    def get_bookmarks(self) -> list[str]:
        return [str(p) for p in self._bookmarks]

    def set_bookmarks(self, paths: list[str]):
        self._bookmarks = [Path(p) for p in paths if p]
        self._save_bookmarks_to_settings()

    def _save_bookmarks_to_settings(self):
        self.settings.set("browser", "bookmarks", self.get_bookmarks())
        self.settings.save()

    def _update_bookmarks_menu(self):
        self.bookmarks_menu.clear()
        if self._root_path and self._root_path not in self._bookmarks:
            action = self.bookmarks_menu.addAction(f"Bookmark '{self._root_path.name}'")
            action.triggered.connect(lambda: self._add_bookmark(self._root_path))
            self.bookmarks_menu.addSeparator()
            
        if not self._bookmarks:
            disabled = self.bookmarks_menu.addAction("(No bookmarks)")
            disabled.setEnabled(False)
        else:
            for path in self._bookmarks:
                action = self.bookmarks_menu.addAction(path.name)
                action.setToolTip(str(path))
                action.triggered.connect(lambda checked, p=path: self.set_root(str(p)))
            self.bookmarks_menu.addSeparator()
            clear_action = self.bookmarks_menu.addAction("Clear Bookmarks")
            clear_action.triggered.connect(self._clear_bookmarks)

    def _add_bookmark(self, path: Path):
        if path not in self._bookmarks:
            self._bookmarks.append(path)
            self._save_bookmarks_to_settings()
            self.bookmarks_changed.emit([str(p) for p in self._bookmarks])

    def _clear_bookmarks(self):
        self._bookmarks.clear()
        self._save_bookmarks_to_settings()
        self.bookmarks_changed.emit([])

    def _on_double_click(self, index):
        source_index = self.proxy_model.mapToSource(index)
        path = self.fs_model.filePath(source_index)
        if self.fs_model.isDir(source_index):
            self.set_root(path)
        else:
            self.file_selected.emit(path)

    def navigate_to(self, path: str):
        self.set_root(path)

    def _show_context_menu(self, point):
        index = self.tree.indexAt(point)
        menu = QMenu(self)

        if index.isValid():
            source_index = self.proxy_model.mapToSource(index)
            path = self.fs_model.filePath(source_index)
            is_dir = self.fs_model.isDir(source_index)
            target_dir = path if is_dir else os.path.dirname(path)

            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self._create_new_file(target_dir))
            menu.addAction(new_file_action)

            new_folder_action = QAction("New Folder", self)
            new_folder_action.triggered.connect(lambda: self._create_new_folder(target_dir))
            menu.addAction(new_folder_action)

            menu.addSeparator()
            if is_dir:
                open_folder = QAction("Open Folder", self)
                open_folder.triggered.connect(lambda: self.set_root(path))
                menu.addAction(open_folder)

            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self._rename_item(index))
            menu.addAction(rename_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self._delete_item(index))
            menu.addAction(delete_action)

        menu.exec(self.tree.mapToGlobal(point))

    def _create_new_file(self, dir_path: str):
        if not dir_path:
            dir_path = str(self._root_path)
        name, ok = QInputDialog.getText(self, "New File", "Filename:", text="untitled.adb")
        if ok and name:
            if not any(name.endswith(e) for e in ADA_EXTENSIONS):
                name += ".adb"
            full_path = os.path.join(dir_path, name)
            try:
                with open(full_path, "w"):
                    pass
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create file:\n{e}")

    def _create_new_folder(self, dir_path: str):
        if not dir_path:
            dir_path = str(self._root_path)
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            full_path = os.path.join(dir_path, name)
            try:
                os.mkdir(full_path)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create folder:\n{e}")

    def _rename_item(self, index):
        self.fs_model.setReadOnly(False)
        self.tree.edit(index)
        self.fs_model.setReadOnly(True)

    def _delete_item(self, index):
        source_index = self.proxy_model.mapToSource(index)
        path = self.fs_model.filePath(source_index)
        is_dir = self.fs_model.isDir(source_index)
        reply = QMessageBox.question(
            self, "Delete", f"Are you sure you want to delete '{os.path.basename(path)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(path) if is_dir else os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete '{os.path.basename(path)}'. {e}")

    def _load_settings(self):
        last_dir = self.settings.get("browser", "last_directory")
        if last_dir and os.path.isdir(last_dir):
            self.navigate_to(last_dir)
        else:
            self.navigate_to(str(Path.home()))
            
        saved_bookmarks = self.settings.get("browser", "bookmarks")
        if saved_bookmarks and isinstance(saved_bookmarks, list):
            self.set_bookmarks(saved_bookmarks)
