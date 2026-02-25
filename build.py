"""
build.py — LOVELACE packaging helper
==================================
Cleans previous build artefacts, then calls PyInstaller to produce a
self-contained binary in dist/LOVELACE/.

The script adds the project venv's site-packages to sys.path BEFORE
invoking PyInstaller so that packages like pyte and ptyprocess are found
even when the system Python (rather than the activated venv) runs this file.

Usage:
    python3 build.py          # with or without venv activated
"""

import importlib.util
import os
import pathlib
import platform
import shutil
import sys

APP_NAME    = "LOVELACE"
ENTRY_POINT = "lovelace/main.py"
SCRIPT_DIR  = pathlib.Path(__file__).parent.resolve()

# Change to the script's directory so build artifacts go to LOVELACE/
os.chdir(SCRIPT_DIR)


# ──────────────────────────────────────────────────────────────────────
# 1. Ensure the venv site-packages are on sys.path so PyInstaller can
#    find all project dependencies regardless of how this script was run.
# ──────────────────────────────────────────────────────────────────────

def _inject_venv_paths() -> None:
    venv_dir = SCRIPT_DIR / "venv"
    if not venv_dir.exists():
        return
    py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_pkgs = venv_dir / "lib" / py_ver / "site-packages"
    if site_pkgs.exists() and str(site_pkgs) not in sys.path:
        sys.path.insert(0, str(site_pkgs))
        print(f"[build] Added venv site-packages to path: {site_pkgs}")

_inject_venv_paths()


# ──────────────────────────────────────────────────────────────────────
# 2. Now import PyInstaller (may come from venv after the path injection)
# ──────────────────────────────────────────────────────────────────────

import PyInstaller.__main__  # noqa: E402  (must be after path injection)


# ──────────────────────────────────────────────────────────────────────
# 3. Helpers
# ──────────────────────────────────────────────────────────────────────

def _find_module_add_data(module_name: str, sep: str = ":") -> list[str]:
    """Return ['--add-data', 'src:dest'] args for a module/package.

    Works for both proper packages (directories) and single-file modules.
    Returns [] with a warning if the module cannot be found.
    """
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"[build] WARNING: '{module_name}' not found — skipping.")
        return []

    if spec.submodule_search_locations:
        # Proper package — bundle the entire directory
        pkg_dir = str(pathlib.Path(spec.origin).parent)
        return ["--add-data", f"{pkg_dir}{sep}{module_name}"]
    else:
        # Single-file module — bundle the .py file into the top-level dir
        return ["--add-data", f"{spec.origin}{sep}."]


def clean_build_dirs() -> None:
    print("Cleaning build directories...")
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)


def get_args() -> list[str]:
    system = platform.system()
    sep    = ";" if system == "Windows" else ":"  # PyInstaller --add-data separator

    args = [
        "--name",    APP_NAME,
        "--clean",
        "--noconfirm",
        "--windowed",
        "--hidden-import", "PyQt6",
        # Explicitly locate pyte and ptyprocess
        *_find_module_add_data("pyte",       sep),
        *_find_module_add_data("ptyprocess", sep),
        "--add-data", f"images{sep}images",
        "--add-data", f"examples{sep}examples",
        "--add-data", f"docs{sep}docs",
    ]

    if system == "Darwin":
        args += ["--target-architecture", "universal2"]
    elif system == "Windows":
        args += ["--icon", f"images{sep}lovelace_icon.png"]

    args.append(ENTRY_POINT)
    return args


# ──────────────────────────────────────────────────────────────────────
# 4. Build
# ──────────────────────────────────────────────────────────────────────

def build() -> None:
    clean_build_dirs()

    args = get_args()

    print(f"Building {APP_NAME} for {platform.system()} …")
    print()

    try:
        PyInstaller.__main__.run(args)
        print()
        print(f"Build complete!  →  dist/{APP_NAME}/")
    except Exception as exc:
        print(f"Build failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    build()
