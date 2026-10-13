"""Marketing exact-text compare. The extract step uses openai.responses in schema.py.

The check asks one question: did every required string appear in the flyer, spelled
and cased exactly? Any text the flyer adds on top of the required copy (a brand name,
a logo wordmark) is reported under ``extra`` for reference but does not fail the check.
Judging whether extra text is a problem is the judge's instruction-following gate, not
this one. Whitespace is normalized before comparing so that OCR spacing quirks do not
cause false misses.
"""

import re

_WHITESPACE = re.compile(r'\s+')


def _normalize(value: str) -> str:
    return _WHITESPACE.sub(' ', value).strip()


def compare_required(extracted: list[str], required_text: list) -> dict:
    got = {_normalize(str(v)) for v in extracted}
    required = [_normalize(str(v)) for v in required_text]
    missing = [v for v in required if v not in got]
    extra = sorted(got - set(required))
    return {
        'pass': not missing,
        'missing': missing,
        'extra': extra,
    }
