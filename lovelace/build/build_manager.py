# lovelace/build/build_manager.py - Compile + Run workflow manager for Ada

import shlex
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

from lovelace.config.settings import Settings


class BuildManager(QObject):
    """Orchestrates the Save → Compile → Run workflow for Ada sources.

    Uses the GNAT Ada Compiler (gnatmake) or compatible.

    GNAT command syntax:
        gnatmake [flags] <source_path> -o <output_path>

    Signals
    -------
    build_started(cmd_str)
        Emitted when a compile begins; carries the full shell command string.
    build_finished(return_code, output_text)
        Emitted when a compile finishes; carries exit code and combined output.
    run_started(executable_path)
        Emitted when the compiled program is sent to the terminal to run.
    """

    build_started = pyqtSignal(str)
    build_finished = pyqtSignal(int, str)
    run_started = pyqtSignal(str)

    def __init__(self, settings: Settings, terminal=None, parent: QObject = None):
        super().__init__(parent)
        self.settings = settings
        self.terminal = terminal          # TerminalWidget (optional at construction)

        self._process: Optional[QProcess] = None
        self._output_buffer: list[str] = []
        self._pending_run: Optional[str] = None   # set by compile_and_run()
        self.last_binary: Optional[str] = None    # updated on every successful build

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self, source_path: str) -> None:
        """Compile *source_path* without running afterwards."""
        self._pending_run = None
        self._start_compile(source_path)

    def compile_and_run(self, source_path: str) -> None:
        """Compile *source_path*, then run it if the build succeeds."""
        output_path = self._get_output_path(source_path)
        self._pending_run = output_path
        self._start_compile(source_path)

    def run(self, executable_path: str) -> None:
        """Send *executable_path* to the terminal PTY to run in the shell."""
        if not self.terminal:
            return
        self.run_started.emit(executable_path)
        # Shell-quote the path so spaces in directory names don't break execution
        quoted = shlex.quote(executable_path)
        self.terminal.write(f"{quoted}\n".encode())

    def clean(self, source_path: str) -> None:
        """Delete the binary and GNAT intermediate files for *source_path*.

        GNAT produces three artefacts per compilation:
          - the binary (no extension)
          - <stem>.o  (object file)
          - <stem>.ali  (Ada Library Information)
        """
        output_path = self._get_output_path(source_path)
        stem = Path(source_path).stem
        out_dir = Path(output_path).parent
        removed = []

        # Binary
        p = Path(output_path)
        if p.exists():
            p.unlink()
            removed.append(str(p))

        # .o object file
        obj = out_dir / f"{stem}.o"
        if obj.exists():
            obj.unlink()
            removed.append(str(obj))

        # .ali unit file
        ali = out_dir / f"{stem}.ali"
        if ali.exists():
            ali.unlink()
            removed.append(str(ali))

        if self.terminal:
            if removed:
                files_list = ", ".join(Path(r).name for r in removed)
                msg = (
                    f"\r\n\033[1;33m[LOVELACE] Cleaned: {files_list}\033[0m\r\n"
                )
            else:
                msg = "\r\n\033[1;33m[LOVELACE] Nothing to clean.\033[0m\r\n"
            self.terminal.on_data_received(msg.encode())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_output_path(self, source_path: str) -> str:
        """Return the output binary path for *source_path*."""
        stem = Path(source_path).stem
        output_dir = self.settings.get("build", "output_dir") or "."
        source_dir = Path(source_path).parent
        out_dir = Path(output_dir)
        if not out_dir.is_absolute():
            out_dir = source_dir / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / stem)

    def _build_command(self, source_path: str):
        """Return (compiler, args_list, output_path) for *source_path*."""
        compiler = self.settings.get("build", "compiler_path") or "gnatmake"
        flags_str = self.settings.get("build", "compiler_flags") or ""
        flags = flags_str.split() if flags_str.strip() else []
        flags = [f.replace("-gl", "-g") if f == "-gl" else f for f in flags]
        output_path = self._get_output_path(source_path)
        args = flags + [source_path, "-o", output_path]
        return compiler, args, output_path

    def _start_compile(self, source_path: str) -> None:
        """Internal: kick off QProcess compilation."""
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            return  # Already compiling

        compiler, args, output_path = self._build_command(source_path)
        cmd_str = compiler + " " + " ".join(args)

        self._output_buffer = []
        self._current_output_path = output_path

        if self.terminal:
            header = (
                f"\r\n\033[1;34m[LOVELACE] Compiling...\033[0m\r\n"
                f"$ {cmd_str}\r\n"
            )
            self.terminal.on_data_received(header.encode())

        self.build_started.emit(cmd_str)

        self._process = QProcess(self)
        self._process.setProgram(compiler)
        self._process.setArguments(args)
        
        # Ensure intermediate files go to the output directory
        out_dir = Path(output_path).parent
        self._process.setWorkingDirectory(str(out_dir))
        
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_compile_finished)
        self._process.start()

    def _on_stdout(self) -> None:
        data = bytes(self._process.readAllStandardOutput())
        self._output_buffer.append(data.decode("utf-8", errors="replace"))
        if self.terminal:
            self.terminal.on_data_received(data)

    def _on_stderr(self) -> None:
        data = bytes(self._process.readAllStandardError())
        self._output_buffer.append(data.decode("utf-8", errors="replace"))
        if self.terminal:
            self.terminal.on_data_received(data)

    def _on_compile_finished(self, exit_code: int, _exit_status) -> None:
        output_text = "".join(self._output_buffer)

        if exit_code == 0:
            self.last_binary = self._current_output_path
            if self.terminal:
                self.terminal.on_data_received(
                    b"\r\n\033[1;32m[LOVELACE] Build successful.\033[0m\r\n"
                )
            pending = self._pending_run
            self._pending_run = None
            if pending:
                self.run(pending)
        else:
            if self.terminal:
                self.terminal.on_data_received(
                    f"\r\n\033[1;31m[LOVELACE] Build failed (exit {exit_code}).\033[0m\r\n"
                    .encode()
                )
            self._pending_run = None

        self.build_finished.emit(exit_code, output_text)
