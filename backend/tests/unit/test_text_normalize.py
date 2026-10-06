"""Tests for PDF text normalization."""

from app.utils.text_normalize import normalize_extracted_text


def test_fixes_decimal_spaces():
    assert normalize_extracted_text("score of 27. 3 BLEU") == "score of 27.3 BLEU"
    assert normalize_extracted_text("Pdrop = 0. 1") == "Pdrop = 0.1"


def test_fixes_hyphenation_line_breaks():
    assert normalize_extracted_text("transduc-\ntion model") == "transduction model"


def test_fixes_ellipsis_artifacts():
    assert normalize_extracted_text("(x1,. , xn)") == "(x1, ..., xn)"


def test_collapses_inline_whitespace():
    assert normalize_extracted_text("too   many    spaces") == "too many spaces"
