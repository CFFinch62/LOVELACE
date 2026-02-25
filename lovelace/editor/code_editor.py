# lovelace/editor/code_editor.py - Code editor widget with line numbers

from __future__ import annotations

from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont, QFontDatabase, QKeyEvent

from lovelace.editor.highlighter import AdaHighlighter
from lovelace.config.settings import Settings
from lovelace.config.themes import Theme, get_theme


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.codeEditor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self._theme: Theme = get_theme(self.settings.get("theme") or "dark")

        self.line_number_area = LineNumberArea(self)
        self.highlighter = AdaHighlighter(self.document(), self._theme)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        self.setup_font()
        self.setup_editor()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.highlighter.set_theme(theme)
        self.highlight_current_line()
        self.line_number_area.update()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_font(self) -> None:
        font_family = self.settings.get("editor", "font_family") or "Monospace"
        font_size = self.settings.get("editor", "font_size") or 14
        font = QFont(font_family, font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

    def setup_editor(self) -> None:
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        tab_width = self.settings.get("editor", "tab_width") or 2
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * tab_width)

    # ------------------------------------------------------------------
    # Auto-indent
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            line_text = cursor.block().text()
            # Collect leading whitespace from the current line
            indent = ""
            for ch in line_text:
                if ch in (' ', '\t'):
                    indent += ch
                else:
                    break
            super().keyPressEvent(event)
            if indent:
                self.insertPlainText(indent)
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Line-number gutter
    # ------------------------------------------------------------------

    def line_number_area_width(self) -> int:
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        return 3 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(self._theme.current_line))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self._theme.line_number_bg))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(self._theme.line_number_fg))
                painter.drawText(
                    0, top,
                    self.line_number_area.width(), self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
