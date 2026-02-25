# lovelace/editor/tab_widget.py - Multi-tab editor widget

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QTabWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal

from lovelace.editor.code_editor import CodeEditor


class EditorTabWidget(QTabWidget):
    """Multi-tab container for CodeEditor instances."""

    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.tab_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_file(self) -> CodeEditor:
        """Open a blank editor tab labelled 'untitled.adb'."""
        editor = CodeEditor()
        index = self.addTab(editor, "untitled.adb")
        self.setCurrentIndex(index)
        editor.modificationChanged.connect(
            lambda modified: self.update_tab_title(editor, modified)
        )
        editor.setFocus()
        return editor

    def open_file(self, path: str | Path, content: str) -> CodeEditor:
        """Open *content* in a new tab titled with the file's base name."""
        path = Path(path)
        editor = CodeEditor()
        editor.setPlainText(content)
        editor.document().setModified(False)
        editor.setProperty("file_path", str(path))

        index = self.addTab(editor, path.name)
        self.setCurrentIndex(index)
        editor.modificationChanged.connect(
            lambda modified: self.update_tab_title(editor, modified)
        )
        editor.setFocus()
        return editor

    def close_tab(self, index: int) -> None:
        editor = self.widget(index)
        if editor is None:
            return
        if editor.document().isModified():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Save changes to '{self.tabText(index).rstrip('*')}'?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                # Emit a signal for the main window to handle the actual save.
                pass
        self.removeTab(index)

    def update_tab_title(self, editor: CodeEditor, modified: bool) -> None:
        index = self.indexOf(editor)
        if index == -1:
            return
        title = self.tabText(index)
        if modified and not title.endswith("*"):
            self.setTabText(index, title + "*")
        elif not modified and title.endswith("*"):
            self.setTabText(index, title[:-1])

    def get_current_editor(self) -> CodeEditor | None:
        return self.currentWidget()
