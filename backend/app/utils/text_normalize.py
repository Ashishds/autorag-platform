"""Normalize text extracted from PDFs and other documents."""

from __future__ import annotations

import re

# "27. 3" / "0. 1" — space inserted between decimal parts during PDF extraction.
_DECIMAL_GAP = re.compile(r"(\d)\.\s+(\d)")
# "word-\ncontinuation" — line-break hyphenation.
_HYPHEN_BREAK = re.compile(r"(\w)-\s*\n\s*(\w)")
# "(x1,. , xn)" — broken ellipsis from two-column PDF layout.
_ELLIPSIS_GAP = re.compile(r",\.\s*,")
# ". ," between tokens — another ellipsis artifact.
_DOT_COMMA = re.compile(r"\.\s+,")
# Runs of spaces/tabs (preserve newlines).
_INLINE_SPACE = re.compile(r"[^\S\n]+")
# More than two consecutive blank lines.
_EXTRA_BLANKS = re.compile(r"\n{3,}")


def normalize_extracted_text(text: str) -> str:
    """Clean common PDF extraction artifacts without changing meaning."""
    if not text:
        return text

    out = _HYPHEN_BREAK.sub(r"\1\2", text)
    out = _DECIMAL_GAP.sub(r"\1.\2", out)
    out = _ELLIPSIS_GAP.sub(", ...,", out)
    out = _DOT_COMMA.sub(",", out)
    out = _INLINE_SPACE.sub(" ", out)
    out = _EXTRA_BLANKS.sub("\n\n", out)
    return out.strip()
