# lovelace/editor/highlighter.py - Ada syntax highlighter

from __future__ import annotations

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

from lovelace.config.themes import Theme, get_theme

# Block-comment state constants
_STATE_NORMAL = 0
_STATE_IN_BRACE_COMMENT = 1    # inside {  }
_STATE_IN_PAREN_COMMENT = 2    # inside (* *)


class AdaHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Ada / Free Ada / Delphi source code.

    Rules are applied in order; later rules override earlier ones on the same
    span of text.  Block comments and line comments are handled last so they
    always win.  All keyword rules are case-insensitive.
    """

    def __init__(self, document, theme: Theme | None = None):
        super().__init__(document)
        self.highlighting_rules: list[tuple] = []
        self._theme: Theme = theme or get_theme("dark")
        self._build_rules(self._theme)

    def set_theme(self, theme: Theme) -> None:
        """Rebuild highlighting rules for *theme* and re-colour the document."""
        self._theme = theme
        self._build_rules(theme)
        self.rehighlight()

    # ------------------------------------------------------------------
    # Rule construction
    # ------------------------------------------------------------------

    def _build_rules(self, theme: Theme) -> None:
        self.highlighting_rules.clear()
        ci = QRegularExpression.PatternOption.CaseInsensitiveOption

        # ── 1. Numbers ────────────────────────────────────────────────
        # Integers, hex ($FF), reals (3.14), exponents (1.5e-3)
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor(theme.number))
        self.highlighting_rules.append((
            QRegularExpression(
                r"\$[0-9A-Fa-f]+\b"                    # hex literal $FF
                r"|\b[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?\b"  # int / real / exp
            ),
            num_fmt,
        ))

        # ── 2. Type-specifier keywords ────────────────────────────────
        type_fmt = QTextCharFormat()
        type_fmt.setForeground(QColor(theme.type_keyword))
        for word in [
            "BOOLEAN", "CHARACTER", "FLOAT", "INTEGER", "NATURAL", "POSITIVE",
            "STRING", "WIDE_CHARACTER", "WIDE_STRING", "DURATION"
        ]:
            self.highlighting_rules.append((
                QRegularExpression(rf"\b{word}\b", ci), type_fmt
            ))

        # ── 3. Control / program-structure keywords (bold) ───────────
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor(theme.keyword))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        for word in [
            "ABORT", "ABS", "ABSTRACT", "ACCEPT", "ACCESS", "ALIASED", "ALL",
            "AND", "ARRAY", "AT", "BEGIN", "BODY", "CASE", "CONSTANT", "DECLARE",
            "DELAY", "DELTA", "DIGITS", "DO", "ELSE", "ELSIF", "END", "ENTRY",
            "EXCEPTION", "EXIT", "FOR", "FUNCTION", "GENERIC", "GOTO", "IF", "IN",
            "INTERFACE", "IS", "LIMITED", "LOOP", "MOD", "NEW", "NOT", "NULL", "OF",
            "OR", "OTHERS", "OUT", "OVERRIDING", "PACKAGE", "PRAGMA", "PRIVATE",
            "PROCEDURE", "PROTECTED", "RAISE", "RANGE", "RECORD", "REM", "RENAMES",
            "REQUEUE", "RETURN", "REVERSE", "SELECT", "SEPARATE", "SOME", "SUBTYPE",
            "SYNCHRONIZED", "TAGGED", "TASK", "TERMINATE", "THEN", "TYPE", "UNTIL",
            "USE", "WHEN", "WHILE", "WITH", "XOR"
        ]:
            self.highlighting_rules.append((
                QRegularExpression(rf"\b{word}\b", ci), kw_fmt
            ))

        # ── 4. Built-in routines / packages ──────────────────────────────
        builtin_fmt = QTextCharFormat()
        builtin_fmt.setForeground(QColor(theme.builtin))
        for word in [
            "ADA", "TEXT_IO", "PUT", "PUT_LINE", "GET", "GET_LINE", "NEW_LINE",
            "INTEGER_TEXT_IO", "FLOAT_TEXT_IO"
        ]:
            self.highlighting_rules.append((
                QRegularExpression(rf"\b{word}\b", ci), builtin_fmt
            ))

        # ── 5. String literals  "…" ───────────────────────────────────
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor(theme.string))
        self.highlighting_rules.append((
            QRegularExpression(r'"([^"]|"")*"'),
            str_fmt,
        ))

        # ── 6. Character literals  '…' ────────────────────────────────
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QColor(theme.string))
        self.highlighting_rules.append((
            QRegularExpression(r"'.?'"),
            char_fmt,
        ))

        # ── 7. Line comments (--) ─────────────────────────────────────
        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor(theme.comment))
        self.highlighting_rules.append((
            QRegularExpression(r"--.*"),
            self._comment_fmt,
        ))

    # ------------------------------------------------------------------
    # Qt override — handles per-line highlighting + multiline comments
    # ------------------------------------------------------------------

    def highlightBlock(self, text: str) -> None:
        # Apply inline rules
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        self.setCurrentBlockState(_STATE_NORMAL)
