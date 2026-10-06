"""TieredPIIService (LLD §9.6). Tier 1 = regex; Tier 2 = optional Gemini Flash verify."""

from __future__ import annotations

from app.services.pii.patterns import (
    CC_RE,
    EMAIL_RE,
    IP_RE,
    PHONE_RE,
    SSN_AADHAAR_RE,
    luhn_valid,
)


class TieredPIIService:
    PII_PATTERNS = {
        "email": EMAIL_RE,
        "phone": PHONE_RE,
        "ssn_aadhaar": SSN_AADHAAR_RE,
        "credit_card": CC_RE,
        "ip": IP_RE,
    }

    def __init__(self, llm=None):
        self._llm = llm  # LLMService, only used for Tier 2

    async def mask(self, text: str, sensitive: bool = False) -> tuple[str, int]:
        masked, n = self._regex_mask(text)
        if sensitive and self._llm is not None:
            masked, extra = await self._llm_verify(masked)
            n += extra
        return masked, n

    def _regex_mask(self, text: str) -> tuple[str, int]:
        count = 0
        for label, pattern in self.PII_PATTERNS.items():

            def make_sub(lbl: str):
                def _sub(m: object) -> str:
                    nonlocal count
                    value = m.group(0)
                    if lbl == "credit_card" and not luhn_valid(value):
                        return value
                    count += 1
                    return f"[{lbl.upper()}]"

                return _sub

            text = pattern.sub(make_sub(label), text)
        return text, count

    async def _llm_verify(self, text: str) -> tuple[str, int]:
        if not text or self._llm is None:
            return text, 0
        prompt = (
            "Analyze the following text and mask any residual Personally Identifiable Information (PII) "
            "like human names, physical addresses, passwords, API keys, or secrets that are not already masked. "
            "Leave already masked tokens like [EMAIL], [IP], [PHONE], [CREDIT_CARD], [SSN_AADHAAR] exactly as they are. "
            "Replace any found residual PII with '[PII]'.\n"
            "Format your response as a JSON object with two fields:\n"
            "1. 'masked_text': the fully masked text string.\n"
            "2. 'extra_pii_count': the integer count of newly masked items.\n\n"
            f"Text to analyze:\n{text}"
        )
        try:
            schema = {
                "type": "OBJECT",
                "properties": {
                    "masked_text": {"type": "STRING"},
                    "extra_pii_count": {"type": "INTEGER"},
                },
                "required": ["masked_text", "extra_pii_count"],
            }
            resp = await self._llm.complete(
                messages=[{"role": "user", "content": prompt}],
                model_preference="gemini-2.5-flash",
                response_schema=schema,
            )
            import json

            data = json.loads(resp.content.strip())
            return data["masked_text"], data["extra_pii_count"]
        except Exception:
            # Fall back gracefully to original text if LLM verification fails
            return text, 0
