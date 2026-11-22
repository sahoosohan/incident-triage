"""Strip sensitive data before any text is sent to a model."""
import re

PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("SECRET", re.compile(r"(?i)\b(password|passwd|pwd|token|api[_-]?key|secret)\s*[=:]\s*\S+")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+\d{1,3}[\s-]?)?\d{5}[\s-]?\d{5}(?!\d)")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

def redact(text: str):
    """Return (clean_text, {label: count})."""
    counts = {}
    for label, pat in PATTERNS:
        def sub(m, label=label):
            counts[label] = counts.get(label, 0) + 1
            if label == "SECRET":
                return f"{m.group(1)}=[REDACTED_SECRET]"
            return f"[REDACTED_{label}]"
        text = pat.sub(sub, text)
    return text, counts
