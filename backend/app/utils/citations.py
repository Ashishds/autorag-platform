"""Normalize LLM answer citations to bracket form [1], [2]."""

from __future__ import annotations

import re

_BOILERPLATE_PREFIXES = (
    "Based on the provided context, ",
    "Based on the provided context ",
    "According to the provided context, ",
    "According to the context, ",
    "From the provided context, ",
)

# Bare footnote digits after a word: "parallelization 5." or "them 15."
_BARE_CITE = re.compile(r"(?<=[a-zA-Z])\s+([1-9]{1,3})([.,;:])")


def strip_answer_boilerplate(text: str) -> str:
    out = text.strip()
    for prefix in _BOILERPLATE_PREFIXES:
        if out.startswith(prefix):
            out = out[len(prefix) :]
            break
    # Capitalize first letter after stripping boilerplate.
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out


def _digits_to_brackets(digits: str, max_source: int) -> str | None:
    if not digits.isdigit() or not digits:
        return None
    if len(digits) == 1:
        n = int(digits)
        return f"[{n}]" if 1 <= n <= max_source else None
    parts: list[str] = []
    for ch in digits:
        n = int(ch)
        if not (1 <= n <= max_source):
            return None
        parts.append(f"[{n}]")
    return "".join(parts)


def normalize_answer_citations(text: str, max_source: int) -> str:
    """Convert bare footnote-style numbers (e.g. 'claim 15.') to '[1][5].'."""
    if max_source <= 0:
        return text

    def _replace(match: re.Match[str]) -> str:
        converted = _digits_to_brackets(match.group(1), max_source)
        if converted is None:
            return match.group(0)
        return f" {converted}{match.group(2)}"

    return _BARE_CITE.sub(_replace, text)


def format_answer(text: str, max_source: int) -> str:
    """Strip boilerplate and normalize citations for display."""
    out = strip_answer_boilerplate(text)
    return normalize_answer_citations(out, max_source)
