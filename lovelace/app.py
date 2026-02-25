# lovelace/app.py - MainWindow

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox,
    QSplitter, QStatusBar, QToolBar, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from lovelace.browser.file_browser import FileBrowser
from lovelace.build.build_manager import BuildManager
from lovelace.config.settings import Settings
from lovelace.config.settings_dialog import SettingsDialog
from lovelace.config.themes import apply_theme_to_app, get_theme
from lovelace.editor.find_replace import FindReplaceDialog
from lovelace.editor.tab_widget import EditorTabWidget
from lovelace.terminal.terminal_widget import TerminalWidget

_OPEN_FILTER = (
    "Ada Files (*.adb *.ads);;"
    "All Files (*)"
)
_SAVE_FILTER = (
    "Ada Body (*.adb);;"
    "Ada Spec (*.ads);;"
    "All Files (*)"
)


class MainWindow(QMainWindow):
    """LOVELACE main application window."""

    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.setWindowTitle("LOVELACE — Ada Teaching Environment")
        self.resize(1024, 768)

        self._setup_ui()
        self._create_toolbar()
        self._load_settings()
        self.apply_theme()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Horizontal splitter: file browser | editor+terminal
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.main_splitter)

        self.file_browser = FileBrowser()
        self.file_browser.file_selected.connect(self.open_file_from_browser)
        self.main_splitter.addWidget(self.file_browser)

        # Vertical splitter: editor | terminal
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.right_splitter)

        self.editor_tabs = EditorTabWidget()
        self.right_splitter.addWidget(self.editor_tabs)

        self.terminal = TerminalWidget()
        self.right_splitter.addWidget(self.terminal)

        self.main_splitter.setSizes([200, 800])
        self.right_splitter.setSizes([500, 268])

        # Build manager (QProcess-based, terminal for output)
        self.build_manager = BuildManager(
            settings=self.settings,
            terminal=self.terminal,
            parent=self,
        )
        self.build_manager.build_started.connect(
            lambda cmd: self.status_bar.showMessage(f"Compiling…  {cmd}")
        )
        self.build_manager.build_finished.connect(self._on_build_finished)
        self.build_manager.run_started.connect(
            lambda path: self.status_bar.showMessage(f"Running: {path}")
        )

        self._create_menus()
        self._setup_status_bar()

    def _create_menus(self) -> None:
        mb = self.menuBar()

        # ── File ──────────────────────────────────────────────────────
        file_menu = mb.addMenu("&File")

        self.new_action = QAction("&New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)

        self.open_action = QAction("&Open…", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)

        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)
        file_menu.addAction(self.save_action)

        save_as_action = QAction("Save &As…", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── Edit ──────────────────────────────────────────────────────
        edit_menu = mb.addMenu("&Edit")

        find_action = QAction("&Find/Replace…", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()

        prefs_action = QAction("&Preferences…", self)
        prefs_action.triggered.connect(self.open_settings)
        edit_menu.addAction(prefs_action)

        # ── View ──────────────────────────────────────────────────────
        view_menu = mb.addMenu("&View")

        self.toggle_browser_action = QAction("Show &File Browser", self)
        self.toggle_browser_action.setCheckable(True)
        self.toggle_browser_action.setChecked(True)
        self.toggle_browser_action.triggered.connect(
            lambda checked: self.file_browser.setVisible(checked)
        )
        view_menu.addAction(self.toggle_browser_action)

        self.toggle_terminal_action = QAction("Show &Terminal", self)
        self.toggle_terminal_action.setCheckable(True)
        self.toggle_terminal_action.setChecked(True)
        self.toggle_terminal_action.triggered.connect(
            lambda checked: self.terminal.setVisible(checked)
        )
        view_menu.addAction(self.toggle_terminal_action)

        # ── Build ─────────────────────────────────────────────────────
        build_menu = mb.addMenu("&Build")

        self.compile_run_action = QAction("Compile && &Run", self)
        self.compile_run_action.setShortcut("Ctrl+R")
        self.compile_run_action.triggered.connect(self.compile_and_run_file)
        build_menu.addAction(self.compile_run_action)

        self.compile_action = QAction("&Compile Only", self)
        self.compile_action.setShortcut("Ctrl+B")
        self.compile_action.triggered.connect(self.compile_file)
        build_menu.addAction(self.compile_action)

        run_last_action = QAction("Run &Last Build", self)
        run_last_action.setShortcut("Ctrl+Shift+R")
        run_last_action.triggered.connect(self.run_last_build)
        build_menu.addAction(run_last_action)

        build_menu.addSeparator()

        clean_action = QAction("Cl&ean Build Output", self)
        clean_action.triggered.connect(self.clean_build)
        build_menu.addAction(clean_action)

        build_menu.addSeparator()

        clear_term_action = QAction("C&lear Terminal Output", self)
        clear_term_action.triggered.connect(self.terminal.clear)
        build_menu.addAction(clear_term_action)

        restart_term_action = QAction("&Restart Terminal", self)
        restart_term_action.triggered.connect(self.terminal.restart)
        build_menu.addAction(restart_term_action)

        interrupt_action = QAction("&Interrupt", self)
        interrupt_action.setShortcut("Ctrl+Shift+C")
        interrupt_action.triggered.connect(self.terminal.interrupt)
        build_menu.addAction(interrupt_action)

        # ── Help ──────────────────────────────────────────────────────
        help_menu = mb.addMenu("&Help")

        about_action = QAction("&About LOVELACE", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.compile_run_action)
        toolbar.addAction(self.compile_action)

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.cursor_label = QLabel("Ln 1, Col 1")
        self.cursor_label.setMinimumWidth(100)
        self.status_bar.addPermanentWidget(self.cursor_label)

        self.status_bar.showMessage("Ready")

        self.editor_tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(0)

    # ------------------------------------------------------------------
    # Cursor / tab tracking
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int) -> None:
        editor = self.editor_tabs.get_current_editor()
        if editor:
            try:
                editor.cursorPositionChanged.disconnect(self.update_cursor_position)
            except (RuntimeError, TypeError):
                pass
            editor.cursorPositionChanged.connect(self.update_cursor_position)
            self.update_cursor_position()
        else:
            self.cursor_label.setText("")

    def update_cursor_position(self) -> None:
        editor = self.editor_tabs.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.cursor_label.setText(f"Ln {line}, Col {col}")

    # ------------------------------------------------------------------
    # Build signal handlers
    # ------------------------------------------------------------------

    def _on_build_finished(self, exit_code: int, _output: str) -> None:
        if exit_code == 0:
            self.status_bar.showMessage("Build succeeded.")
        else:
            self.status_bar.showMessage(f"Build failed (exit {exit_code}).")

    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------

    def new_file(self) -> None:
        self.editor_tabs.new_file()

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Ada File", "", _OPEN_FILTER
        )
        if not path:
            return
        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")
            self.editor_tabs.open_file(p, content)
            self.status_bar.showMessage(f"Opened {p.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{exc}")

    def open_file_from_browser(self, path: str) -> None:
        try:
            p = Path(path)
            content = p.read_text(encoding="utf-8")
            self.editor_tabs.open_file(p, content)
            self.status_bar.showMessage(f"Opened {p.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{exc}")

    def save_file(self) -> None:
        editor = self.editor_tabs.get_current_editor()
        if not editor:
            return
        file_path = editor.property("file_path")
        if file_path:
            self.save_file_to_path(editor, file_path)
        else:
            self.save_file_as()

    def save_file_as(self) -> None:
        editor = self.editor_tabs.get_current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Ada File", "", _SAVE_FILTER
        )
        if path:
            self.save_file_to_path(editor, path)

    def save_file_to_path(self, editor, path: str) -> None:
        try:
            p = Path(path)
            p.write_text(editor.toPlainText(), encoding="utf-8")
            editor.setProperty("file_path", str(p))
            editor.document().setModified(False)
            idx = self.editor_tabs.indexOf(editor)
            self.editor_tabs.setTabText(idx, p.name)
            self.status_bar.showMessage(f"Saved {p.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{exc}")

    # ------------------------------------------------------------------
    # Edit / preferences actions
    # ------------------------------------------------------------------

    def show_find_replace(self) -> None:
        editor = self.editor_tabs.get_current_editor()
        if editor:
            dialog = FindReplaceDialog(editor, self)
            dialog.show()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.apply_theme()

    def apply_theme(self) -> None:
        theme_name = self.settings.get("theme")
        theme = get_theme(theme_name)
        apply_theme_to_app(QApplication.instance(), theme)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About LOVELACE",
            "LOVELACE — Ada Teaching Environment\n"
            "Version 0.1.0\n\n"
            "A beginner-friendly IDE for learning and teaching Ada.\n\n"
            "\u00a9 2025–2026 Chuck Finch — Fragillidae Software",
        )

    # ------------------------------------------------------------------
    # Build actions
    # ------------------------------------------------------------------

    def _ensure_saved(self) -> str | None:
        """Return the file path of the current editor, saving first if needed.

        Returns *None* if there is no current editor, the file has never been
        saved (user cancels Save As), or the user dismisses the prompt.
        """
        editor = self.editor_tabs.get_current_editor()
        if not editor:
            self.status_bar.showMessage("No file open.")
            return None

        file_path = editor.property("file_path")

        # Unsaved new file — must save before compiling
        if not file_path:
            ans = QMessageBox.question(
                self,
                "Save before compiling",
                "The file must be saved before compiling.\nSave now?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
            )
            if ans == QMessageBox.StandardButton.Save:
                self.save_file_as()
                file_path = editor.property("file_path")
            if not file_path:
                return None

        # Modified but already saved — auto-save silently
        if editor.document().isModified():
            self.save_file_to_path(editor, file_path)

        return file_path

    def compile_file(self) -> None:
        path = self._ensure_saved()
        if path:
            self.build_manager.compile(path)

    def compile_and_run_file(self) -> None:
        path = self._ensure_saved()
        if path:
            self.build_manager.compile_and_run(path)

    def run_last_build(self) -> None:
        binary = self.build_manager.last_binary
        if binary:
            self.build_manager.run(binary)
        else:
            self.status_bar.showMessage("No previous build to run.")

    def clean_build(self) -> None:
        editor = self.editor_tabs.get_current_editor()
        if not editor:
            self.status_bar.showMessage("No file open.")
            return
        file_path = editor.property("file_path")
        if file_path:
            self.build_manager.clean(file_path)
        else:
            self.status_bar.showMessage("File has never been saved — nothing to clean.")

    # ------------------------------------------------------------------
    # Window state
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        geometry = self.settings.get("window", "geometry")
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

        splitter_state = self.settings.get("window", "splitter_state")
        if splitter_state:
            self.main_splitter.restoreState(bytes.fromhex(splitter_state))

        right_state = self.settings.get("window", "right_splitter_state")
        if right_state:
            self.right_splitter.restoreState(bytes.fromhex(right_state))

    def closeEvent(self, event) -> None:  # noqa: N802
        # Persist window geometry and splitter positions
        self.settings.set(
            "window", "geometry",
            self.saveGeometry().toHex().data().decode(),
        )
        self.settings.set(
            "window", "splitter_state",
            self.main_splitter.saveState().toHex().data().decode(),
        )
        self.settings.set(
            "window", "right_splitter_state",
            self.right_splitter.saveState().toHex().data().decode(),
        )
        self.settings.save()

        # Shut down PTY cleanly
        self.terminal.pty.terminate_process()
        self.terminal.pty.wait(2000)

        event.accept()
