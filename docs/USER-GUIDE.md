# LOVELACE User Guide

Welcome to **LOVELACE** (Better Libre Atelier for the Z-machine Environment — Ada IDE), a beginner-friendly IDE for learning and writing Ada. This guide covers installation, the interface, and all major features.

---

## 1. Installation and Running

### Prerequisites

- **Python 3.10+** — check with `python3 --version`
- **Free Ada Compiler (gnatmake)** — recommended:

  | Platform         | Command                                                                  |
  | ---------------- | ------------------------------------------------------------------------ |
  | Debian / Ubuntu  | `sudo apt install gnatmake`                                                   |
  | Fedora / RHEL    | `sudo dnf install gnatmake`                                                   |
  | macOS (Homebrew) | `brew install gnatmake`                                                       |
  | Windows          | Download from [freeada.org](https://www.freeada.org/download.html) |

### Starting LOVELACE

1. Open a terminal in the LOVELACE project directory.
2. Run the launch script:
   ```bash
   ./run.sh
   ```
   The script automatically creates a Python virtual environment, installs all dependencies, and starts the application.

### Command-Line Options

```bash
python3 -m lovelace.main           # launch normally
python3 -m lovelace.main --version # print version and exit
```

---

## 2. Interface Overview

The LOVELACE window is divided into three panels:

1. **File Browser (Left)** — navigate directories; filtered to Ada source files by default.
2. **Code Editor (Center/Top)** — multi-tab editor with syntax highlighting and line numbers.
3. **Terminal (Bottom)** — a full interactive shell (bash) for building and running programs.

### Menu Bar

| Menu      | Key actions                                                                                           |
| --------- | ----------------------------------------------------------------------------------------------------- |
| **File**  | New · Open · Save · Save As · Exit                                                                    |
| **Edit**  | Find/Replace · Preferences                                                                            |
| **View**  | Show/Hide File Browser · Show/Hide Terminal                                                           |
| **Build** | Compile & Run · Compile Only · Run Last Build · Clean · Clear Terminal · Restart Terminal · Interrupt |
| **Help**  | About LOVELACE                                                                                           |

---

## 3. Code Editor

- **Syntax Highlighting** — Ada keywords, types, built-ins, compiler directives, strings, and multiline comments (`{ }` and `(* *)`) are all color-coded. The highlighter uses a state machine for accurate multiline comment detection.
- **Line Numbers** — displayed in the left gutter; updates as you type.
- **Multi-Tab Editing** — open any number of `.adb` files simultaneously. Tabs show a `*` when a file has unsaved changes.
- **Auto-Indent** — pressing Enter preserves the current indentation level.
- **Find & Replace** — open with `Ctrl+F`. Supports case-sensitive toggle, wrap-around, Replace, and Replace All.

---

## 4. Build System

LOVELACE compiles Ada programs using **gnatmake** (Free Ada Compiler). Output streams live into the terminal as it arrives.

### Workflow

1. Open or create a `.adb` file in the editor.
2. Press **`Ctrl+R`** (Compile & Run) or choose **Build → Compile & Run**.
   - LOVELACE auto-saves the file before compiling.
   - The compiler command and output appear in the terminal.
   - On success, the binary runs immediately in the terminal.
3. Use **`Ctrl+B`** (Compile Only) to check for errors without running.
4. Use **Build → Run Last Build** to re-run the most recently compiled binary.
5. Use **Build → Clean** to delete the compiled binary and intermediate `.ppu`/`.o` files.

### Compiler Command

```bash
gnatmake -o<output_path> <source.adb>
```

Extra flags (e.g., `-O2 -Xs`) can be set in **Preferences → Build → Compiler Flags**.

### Compiler Error Format

gnatmake reports errors as:
```
source.adb(5,12) Error: Undefined identifier: 'Foo'
```
These appear in the terminal panel with the standard LOVELACE colour headers (blue = compiling, green = success, red = failure).

---

## 5. Integrated Terminal

The bottom panel is a full PTY shell backed by your system's `$SHELL`.

- **Interactive** — type any shell command and press Enter.
- **Ctrl+C** — if text is selected, copies it. Otherwise sends SIGINT to the running process.
- **Ctrl+D** — sends EOF (exits the shell or terminates input).
- **Mouse selection** — click and drag to select text; right-click for a Copy context menu.
- **Restart Terminal** — **Build → Restart Terminal** kills and relaunches the shell.
- **Clear Terminal** — **Build → Clear Terminal** wipes the visible output.

---

## 6. File Browser

- **Navigation** — double-click folders to navigate into them.
- **Open files** — double-click a Ada file to open it in a new editor tab.
- **Filtered view** — shows only Ada source files (`.adb`, `.pp`, `.p`, `.inc`, `.lpr`) by default.
- **Context menu** — right-click to create a new file (defaults to `untitled.adb`), new folder, rename, or delete.

---

## 7. Preferences

Open with **Edit → Preferences**.

### Editor Tab
| Setting           | Description                                                |
| ----------------- | ---------------------------------------------------------- |
| Font family       | Monospace font used in the editor and terminal             |
| Font size         | Point size (default: 14)                                   |
| Tab width         | Spaces per indent level (default: 2 per Ada convention) |
| Show line numbers | Toggle the gutter on/off                                   |

### Build Tab
| Setting          | Description                                               |
| ---------------- | --------------------------------------------------------- |
| Compiler         | Auto-detected Ada compilers; use custom path if needed |
| Compiler Flags   | Additional gnatmake flags (e.g., `-O2 -Xs -Scm`)               |
| Output directory | Where to place compiled binaries (`.` = same as source)   |

### Appearance Tab
| Setting | Description                     |
| ------- | ------------------------------- |
| Theme   | **Dark** (default) or **Light** |

---

## 8. Example Programs

LOVELACE ships with eight ready-to-run programs in the `examples/` folder. Open any one in the file browser, then press `Ctrl+R`.

| File               | Topic                                                  |
| ------------------ | ------------------------------------------------------ |
| `hello_world.adb`  | Classic first program — `WriteLn`                      |
| `variables.adb`    | Integer, Real, Char, String, Boolean                   |
| `loops.adb`        | `for`, `while`, `repeat…until`                         |
| `conditionals.adb` | `if/then/else`, `case` statement                       |
| `procedures.adb`   | `procedure`, `function`, parameters, recursion         |
| `arrays.adb`       | Static arrays, loops, min/max                          |
| `records.adb`      | `record` type, field access                            |
| `fileio.adb`       | Text file read/write with `Assign`, `Reset`, `Rewrite` |

---

## 9. Keyboard Shortcuts

| Action            | Shortcut                 |
| ----------------- | ------------------------ |
| New file          | `Ctrl+N`                 |
| Open file         | `Ctrl+O`                 |
| Save              | `Ctrl+S`                 |
| Save As           | `Ctrl+Shift+S`           |
| Find / Replace    | `Ctrl+F`                 |
| Compile & Run     | `Ctrl+R`                 |
| Compile Only      | `Ctrl+B`                 |
| Interrupt process | `Ctrl+C` (no selection)  |
| Copy selection    | `Ctrl+C` (text selected) |

---

## 10. Troubleshooting

**"No compilers found" in Preferences**
Ensure `gnatmake` is installed and on your `PATH`. After installing, click **Refresh** in the Build tab. Use **Custom Path** to point to a non-standard location.

**Build fails with "command not found"**
Run `which gnatmake` in a terminal. If not found, install Free Ada. On macOS, `brew install gnatmake` installs to `/opt/homebrew/bin/gnatmake`.

**Compile succeeds but nothing runs**
Check the output directory — the binary may be in a sub-directory if you changed that setting. Try **Build → Run Last Build** after a successful compile.

**Multiline comment not highlighted correctly**
LOVELACE's highlighter tracks `{ }` and `(* *)` block comment state across lines. If a comment is not terminating, check for a missing `}` or `*)`.

**Window layout not restored**
Delete `~/.config/lovelace/settings.json` — LOVELACE will recreate it with defaults on the next launch.
