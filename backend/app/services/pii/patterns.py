"""Tier-1 PII regexes (hoisted to module scope — compiled once)."""

import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{4}")
SSN_AADHAAR_RE = re.compile(r"\b(?:\d{3}-\d{2}-\d{4}|\d{4}\s?\d{4}\s?\d{4})\b")
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if not 13 <= len(digits) <= 16:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0
