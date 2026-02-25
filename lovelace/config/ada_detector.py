"""
Ada compiler detection module.

Detects common Ada compilers installed on the system.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class AdaCompiler:
    """Represents a detected Ada compiler."""
    name: str        # Human-readable name, e.g. "Free Ada Compiler"
    path: str        # Absolute path to the executable
    version: Optional[str] = None

    def display_name(self) -> str:
        """Return a user-friendly display name."""
        if self.version:
            return f"{self.name} ({self.version})"
        return self.name


# Compilers to detect, in preference order.
# Format: (command, display_name, version_args, version_parser)
KNOWN_COMPILERS = [
    (
        "gnatmake",
        "GNAT Ada Compiler",
        ["--version"],
        lambda out: out.split("\n")[0].strip() if out else None,
    ),
]

def _get_compiler_version(
    path: str, version_args: list, version_parser
) -> Optional[str]:
    """Try to retrieve the version string for a compiler."""
    if not version_args or not version_parser:
        return None
    try:
        result = subprocess.run(
            [path] + version_args,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout or result.stderr
        if output:
            return version_parser(output)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    return None


def detect_ada_compilers() -> list[AdaCompiler]:
    """
    Detect all Ada compilers installed on the system.

    Returns:
        A list of AdaCompiler objects in preference order,
        with duplicates (same binary path) removed.
    """
    detected: list[AdaCompiler] = []
    seen_paths: set[str] = set()

    for cmd, display_name, version_args, version_parser in KNOWN_COMPILERS:
        path = shutil.which(cmd)
        if path and path not in seen_paths:
            seen_paths.add(path)
            version = _get_compiler_version(path, version_args, version_parser)
            detected.append(
                AdaCompiler(name=display_name, path=path, version=version)
            )

    return detected


def get_default_compiler() -> Optional[AdaCompiler]:
    """
    Return the preferred Ada compiler (first in preference order).

    Returns:
        A AdaCompiler, or None if nothing is installed.
    """
    compilers = detect_ada_compilers()
    return compilers[0] if compilers else None


def is_valid_compiler(path: str) -> bool:
    """
    Check whether *path* points to a valid, executable compiler.

    Args:
        path: Absolute or relative path to the compiler binary.

    Returns:
        True if the file exists and is executable.
    """
    if not path:
        return False
    if os.path.isabs(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)
    return shutil.which(path) is not None
