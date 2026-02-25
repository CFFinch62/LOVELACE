# lovelace/terminal/terminal_widget.py - Terminal display widget (pyte + PTY)

import os

import pyte
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import (
    QPainter, QFont, QColor, QFontMetrics, QKeyEvent, QBrush,
    QMouseEvent, QGuiApplication,
)

from lovelace.terminal.pty_process import PTYProcess
from lovelace.config.settings import Settings


class TerminalWidget(QWidget):
    """PTY-backed terminal panel using pyte for VT100 emulation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()

        # Terminal dimensions (updated on resize)
        self.cols = 80
        self.rows = 24

        # pyte screen + stream
        self.screen = pyte.Screen(self.cols, self.rows)
        self.stream = pyte.Stream(self.screen)

        # PTY process — always starts the system shell
        shell = os.environ.get("SHELL", "/bin/bash")
        self.pty = PTYProcess(command=[shell])
        self.pty.data_received.connect(self.on_data_received)
        self.pty.process_exited.connect(self.on_process_exited)

        # Font
        self.setup_font()

        # Blinking cursor
        self.cursor_visible = True
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self.toggle_cursor)
        self.cursor_timer.start(500)

        # Mouse selection state
        self._sel_start: tuple[int, int] | None = None  # (row, col)
        self._sel_end:   tuple[int, int] | None = None
        self._selecting = False

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Launch the shell
        self.pty.start()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_font(self) -> None:
        font_family = self.settings.get("editor", "font_family") or "Monospace"
        font_size = self.settings.get("editor", "font_size") or 14

        self.font = QFont(font_family, font_size)
        self.font.setStyleHint(QFont.StyleHint.Monospace)
        self.fm = QFontMetrics(self.font)

        self.char_width = self.fm.horizontalAdvance("W")
        self.char_height = self.fm.height()

        self.resize_terminal()

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resizeEvent(self, event) -> None:
        self.resize_terminal()
        super().resizeEvent(event)

    def resize_terminal(self) -> None:
        new_cols = max(1, self.width() // self.char_width)
        new_rows = max(1, self.height() // self.char_height)

        if new_cols != self.cols or new_rows != self.rows:
            self.cols = new_cols
            self.rows = new_rows
            self.screen.resize(self.rows, self.cols)
            self.pty.resize(self.rows, self.cols)
            self.update()

    # ------------------------------------------------------------------
    # PTY callbacks
    # ------------------------------------------------------------------

    def on_data_received(self, data: bytes) -> None:
        try:
            self.stream.feed(data.decode("utf-8", errors="replace"))
            self.update()
        except Exception:
            pass

    def on_process_exited(self, exit_code: int) -> None:
        self.stream.feed(f"\r\n[Process exited with code {exit_code}]\r\n")
        self.update()

    def write(self, data: bytes) -> None:
        """Send *data* to the PTY (used by BuildManager to run programs)."""
        self.pty.write(data)

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        text = event.text()
        mods = event.modifiers()

        if key == Qt.Key.Key_Return:
            self.write(b"\r")
        elif key == Qt.Key.Key_Backspace:
            self.write(b"\x7f")
        elif key == Qt.Key.Key_Tab:
            self.write(b"\t")
        elif key == Qt.Key.Key_Up:
            self.write(b"\x1b[A")
        elif key == Qt.Key.Key_Down:
            self.write(b"\x1b[B")
        elif key == Qt.Key.Key_Right:
            self.write(b"\x1b[C")
        elif key == Qt.Key.Key_Left:
            self.write(b"\x1b[D")
        elif mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            # Copy if text is selected; otherwise send SIGINT (like modern terminals)
            if self._get_sel_range() is not None:
                self.copy_selection()
            else:
                self.write(b"\x03")
        elif mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_D:
            self.write(b"\x04")   # EOF
        elif text:
            self.write(text.encode("utf-8"))

    # ------------------------------------------------------------------
    # Mouse selection
    # ------------------------------------------------------------------

    def _pixel_to_cell(self, pos: QPoint) -> tuple[int, int]:
        """Convert a pixel position to (row, col) in the terminal grid."""
        col = max(0, min(self.cols - 1, pos.x() // self.char_width))
        row = max(0, min(self.rows - 1, pos.y() // self.char_height))
        return (row, col)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._pixel_to_cell(event.pos())
            self._sel_start = cell
            self._sel_end   = cell
            self._selecting = True
            self.update()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._selecting and event.buttons() & Qt.MouseButton.LeftButton:
            self._sel_end = self._pixel_to_cell(event.pos())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._selecting = False
            if self._sel_start == self._sel_end:
                # Single click with no drag — clear selection
                self._sel_start = None
                self._sel_end   = None
            self.update()

    def _get_sel_range(self) -> tuple[tuple[int,int], tuple[int,int]] | None:
        """Return normalised (start, end) cells or None if no selection."""
        if self._sel_start is None or self._sel_end is None:
            return None
        s, e = self._sel_start, self._sel_end
        if (s[0], s[1]) > (e[0], e[1]):
            s, e = e, s
        return s, e

    def _cell_in_selection(self, row: int, col: int) -> bool:
        sel = self._get_sel_range()
        if sel is None:
            return False
        (sr, sc), (er, ec) = sel
        if row < sr or row > er:
            return False
        if row == sr and col < sc:
            return False
        if row == er and col > ec:
            return False
        return True

    def copy_selection(self) -> None:
        """Copy the selected text to the system clipboard."""
        sel = self._get_sel_range()
        if sel is None:
            return
        (sr, sc), (er, ec) = sel
        lines = []
        for row in range(sr, er + 1):
            row_chars = self.screen.buffer[row]
            c_start = sc if row == sr else 0
            c_end   = ec if row == er else self.cols - 1
            line = "".join(row_chars[c].data for c in range(c_start, c_end + 1))
            lines.append(line.rstrip())
        text = "\n".join(lines)
        if text:
            QGuiApplication.clipboard().setText(text)

    def _show_context_menu(self, point: QPoint) -> None:
        menu = QMenu(self)
        copy_act = menu.addAction("Copy")
        copy_act.setEnabled(self._get_sel_range() is not None)
        copy_act.triggered.connect(self.copy_selection)
        menu.exec(self.mapToGlobal(point))

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setFont(self.font)

        bg_color  = QColor("#0f0f0f")
        fg_color  = QColor("#cccccc")
        sel_color = QColor(0, 120, 200, 120)   # translucent blue selection

        painter.fillRect(self.rect(), bg_color)

        for y in range(self.rows):
            row_chars = self.screen.buffer[y]
            for x in range(self.cols):
                char_data = row_chars[x]

                # Selection highlight
                if self._cell_in_selection(y, x):
                    painter.fillRect(
                        x * self.char_width,
                        y * self.char_height,
                        self.char_width,
                        self.char_height,
                        sel_color,
                    )

                painter.setPen(fg_color)
                painter.drawText(
                    x * self.char_width,
                    y * self.char_height + self.fm.ascent(),
                    char_data.data,
                )

        # Blinking block cursor
        if self.cursor_visible and self.pty.running:
            cx = self.screen.cursor.x
            cy = self.screen.cursor.y
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(200, 200, 200, 100)))
            painter.drawRect(
                cx * self.char_width,
                cy * self.char_height,
                self.char_width,
                self.char_height,
            )

    def toggle_cursor(self) -> None:
        self.cursor_visible = not self.cursor_visible
        cx = self.screen.cursor.x
        cy = self.screen.cursor.y
        self.update(
            cx * self.char_width, cy * self.char_height,
            self.char_width, self.char_height,
        )

    # ------------------------------------------------------------------
    # Public actions (wired to menu in MainWindow)
    # ------------------------------------------------------------------

    def restart(self) -> None:
        """Kill the current shell and start a fresh one."""
        self.pty.terminate_process()
        self.pty.wait()
        self.screen.reset()
        self._sel_start = None
        self._sel_end   = None

        shell = os.environ.get("SHELL", "/bin/bash")
        self.pty = PTYProcess(command=[shell])
        self.pty.data_received.connect(self.on_data_received)
        self.pty.process_exited.connect(self.on_process_exited)
        self.pty.start()
        self.pty.resize(self.rows, self.cols)
        self.update()

    def clear(self) -> None:
        """Clear the terminal screen buffer."""
        self.screen.reset()
        self._sel_start = None
        self._sel_end   = None
        self.update()

    def interrupt(self) -> None:
        """Send Ctrl+C to the foreground process."""
        self.write(b"\x03")

    # ------------------------------------------------------------------
    # Focus
    # ------------------------------------------------------------------

    def focusInEvent(self, event) -> None:
        self.cursor_visible = True
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
