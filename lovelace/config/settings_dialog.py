# lovelace/config/settings_dialog.py - Preferences dialog

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QSpinBox, QCheckBox, QComboBox,
    QDialogButtonBox, QLineEdit, QFileDialog, QPushButton,
    QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from lovelace.config.ada_detector import (
    detect_ada_compilers, is_valid_compiler,
)


class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Preferences")
        self.resize(520, 420)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._create_editor_tab()
        self._create_build_tab()
        self._create_appearance_tab()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._load_values()

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _create_editor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Font Family
        h = QHBoxLayout()
        h.addWidget(QLabel("Font Family:"))
        self.font_family_edit = QLineEdit()
        h.addWidget(self.font_family_edit)
        layout.addLayout(h)

        # Font Size
        h = QHBoxLayout()
        h.addWidget(QLabel("Font Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        h.addWidget(self.font_size_spin)
        layout.addLayout(h)

        # Tab Width
        h = QHBoxLayout()
        h.addWidget(QLabel("Tab Width:"))
        self.tab_width_spin = QSpinBox()
        self.tab_width_spin.setRange(1, 16)
        h.addWidget(self.tab_width_spin)
        layout.addLayout(h)

        # Show Line Numbers
        self.line_numbers_check = QCheckBox("Show Line Numbers")
        layout.addWidget(self.line_numbers_check)

        layout.addStretch()
        self.tabs.addTab(tab, "Editor")

    def _create_build_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Compiler group
        compiler_group = QGroupBox("Ada Compiler")
        cg_layout = QVBoxLayout(compiler_group)

        # Detected compilers dropdown
        h = QHBoxLayout()
        h.addWidget(QLabel("Compiler:"))
        self.compiler_combo = QComboBox()
        self.compiler_combo.setMinimumWidth(260)
        self.compiler_combo.currentIndexChanged.connect(self._on_compiler_changed)
        h.addWidget(self.compiler_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Re-scan for installed Ada compilers")
        refresh_btn.clicked.connect(self._refresh_compilers)
        h.addWidget(refresh_btn)
        cg_layout.addLayout(h)

        # Custom path
        h = QHBoxLayout()
        self.custom_path_check = QCheckBox("Use custom path:")
        self.custom_path_check.toggled.connect(self._on_custom_path_toggled)
        h.addWidget(self.custom_path_check)

        self.compiler_path_edit = QLineEdit()
        self.compiler_path_edit.setEnabled(False)
        self.compiler_path_edit.setPlaceholderText("Path to Ada compiler executable")
        h.addWidget(self.compiler_path_edit)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_compiler)
        h.addWidget(browse_btn)
        cg_layout.addLayout(h)

        layout.addWidget(compiler_group)

        # Compiler flags
        h = QHBoxLayout()
        h.addWidget(QLabel("Compiler Flags:"))
        self.compiler_flags_edit = QLineEdit()
        self.compiler_flags_edit.setPlaceholderText("-O2 -g")
        h.addWidget(self.compiler_flags_edit)
        layout.addLayout(h)

        # Output directory
        h = QHBoxLayout()
        h.addWidget(QLabel("Output Directory:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText(".")
        h.addWidget(self.output_dir_edit)

        out_browse_btn = QPushButton("Browse…")
        out_browse_btn.clicked.connect(self._browse_output_dir)
        h.addWidget(out_browse_btn)
        layout.addLayout(h)

        layout.addStretch()
        self.tabs.addTab(tab, "Build")

        # Populate compiler list
        self._refresh_compilers()

    def _create_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        h = QHBoxLayout()
        h.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        h.addWidget(self.theme_combo)
        layout.addLayout(h)

        layout.addStretch()
        self.tabs.addTab(tab, "Appearance")

    # ------------------------------------------------------------------
    # Compiler helpers
    # ------------------------------------------------------------------

    def _refresh_compilers(self):
        self.compiler_combo.clear()
        self._detected_compilers = detect_ada_compilers()

        if not self._detected_compilers:
            self.compiler_combo.addItem("No compilers found", "")
            self.compiler_combo.setEnabled(False)
            self.custom_path_check.setChecked(True)
            self.custom_path_check.setEnabled(False)
        else:
            self.compiler_combo.setEnabled(True)
            self.custom_path_check.setEnabled(True)
            for compiler in self._detected_compilers:
                self.compiler_combo.addItem(compiler.display_name(), compiler.path)

    def _on_compiler_changed(self, index):
        if not self.custom_path_check.isChecked() and index >= 0:
            path = self.compiler_combo.currentData()
            if path:
                self.compiler_path_edit.setText(path)

    def _on_custom_path_toggled(self, checked):
        self.compiler_path_edit.setEnabled(checked)
        self.compiler_combo.setEnabled(not checked)
        if not checked and self.compiler_combo.currentData():
            self.compiler_path_edit.setText(self.compiler_combo.currentData())

    def _browse_compiler(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Ada Compiler Executable"
        )
        if path:
            self.compiler_path_edit.setText(path)
            self.custom_path_check.setChecked(True)

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_edit.text() or "."
        )
        if directory:
            self.output_dir_edit.setText(directory)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_values(self):
        # Editor
        self.font_family_edit.setText(
            self.settings.get("editor", "font_family") or ""
        )
        self.font_size_spin.setValue(
            self.settings.get("editor", "font_size") or 14
        )
        self.tab_width_spin.setValue(
            self.settings.get("editor", "tab_width") or 3
        )
        self.line_numbers_check.setChecked(
            bool(self.settings.get("editor", "show_line_numbers"))
        )

        # Build
        saved_path = self.settings.get("build", "compiler_path") or ""
        self.compiler_path_edit.setText(saved_path)
        found_match = False
        for i in range(self.compiler_combo.count()):
            if self.compiler_combo.itemData(i) == saved_path:
                self.compiler_combo.setCurrentIndex(i)
                found_match = True
                break
        if not found_match and saved_path:
            self.custom_path_check.setChecked(True)

        self.compiler_flags_edit.setText(
            self.settings.get("build", "compiler_flags") or ""
        )
        self.output_dir_edit.setText(
            self.settings.get("build", "output_dir") or "."
        )

        # Appearance
        current_theme = self.settings.get("theme") or "dark"
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def _save_values(self):
        # Editor
        self.settings.set("editor", "font_family", self.font_family_edit.text())
        self.settings.set("editor", "font_size", self.font_size_spin.value())
        self.settings.set("editor", "tab_width", self.tab_width_spin.value())
        self.settings.set(
            "editor", "show_line_numbers", self.line_numbers_check.isChecked()
        )

        # Build
        self.settings.set(
            "build", "compiler_path", self.compiler_path_edit.text()
        )
        self.settings.set(
            "build", "compiler_flags", self.compiler_flags_edit.text()
        )
        self.settings.set(
            "build", "output_dir", self.output_dir_edit.text() or "."
        )

        # Appearance
        self.settings.set("theme", self.theme_combo.currentText())

        self.settings.save()

    def accept(self):
        compiler_path = self.compiler_path_edit.text()
        if compiler_path and not is_valid_compiler(compiler_path):
            result = QMessageBox.warning(
                self,
                "Invalid Compiler",
                f"The path '{compiler_path}' does not appear to be a valid "
                f"executable.\n\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.No:
                return

        self._save_values()
        super().accept()
