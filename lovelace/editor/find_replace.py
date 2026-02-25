# lovelace/editor/find_replace.py - Find and Replace dialog

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextDocument


class FindReplaceDialog(QDialog):
    """Non-modal Find / Replace dialog attached to a CodeEditor."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find / Replace")
        self.setFixedWidth(420)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)

        # Find row
        h_find = QHBoxLayout()
        h_find.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self.find_next)
        h_find.addWidget(self.find_input)
        layout.addLayout(h_find)

        # Replace row
        h_replace = QHBoxLayout()
        h_replace.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        h_replace.addWidget(self.replace_input)
        layout.addLayout(h_replace)

        # Options
        self.case_check = QCheckBox("Case Sensitive")
        layout.addWidget(self.case_check)

        # Buttons
        btn_layout = QHBoxLayout()

        find_next_btn = QPushButton("Find Next")
        find_next_btn.clicked.connect(self.find_next)
        btn_layout.addWidget(find_next_btn)

        find_prev_btn = QPushButton("Find Previous")
        find_prev_btn.clicked.connect(self.find_previous)
        btn_layout.addWidget(find_prev_btn)

        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace)
        btn_layout.addWidget(replace_btn)

        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        btn_layout.addWidget(replace_all_btn)

        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_flags(self, backward: bool = False) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case_check.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def find_next(self) -> None:
        text = self.find_input.text()
        if not text:
            return
        flags = self._find_flags()
        found = self.editor.find(text, flags)
        if not found:
            # Wrap around to the beginning
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(text, flags)
            if not found:
                QMessageBox.information(self, "Find", "Text not found.")

    def find_previous(self) -> None:
        text = self.find_input.text()
        if not text:
            return
        flags = self._find_flags(backward=True)
        found = self.editor.find(text, flags)
        if not found:
            # Wrap around to the end
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(text, flags)
            if not found:
                QMessageBox.information(self, "Find", "Text not found.")

    def replace(self) -> None:
        cursor = self.editor.textCursor()
        search = self.find_input.text()
        selected = cursor.selectedText()

        match = (
            selected.lower() == search.lower()
            if not self.case_check.isChecked()
            else selected == search
        )

        if cursor.hasSelection() and match:
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self) -> None:
        text = self.find_input.text()
        if not text:
            return
        replacement = self.replace_input.text()
        flags = self._find_flags()
        count = 0

        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

        while self.editor.find(text, flags):
            self.editor.textCursor().insertText(replacement)
            count += 1

        cursor.endEditBlock()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrence(s).")
