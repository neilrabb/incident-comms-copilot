"""Shared utilities."""

import re
from datetime import datetime, timezone
from typing import Optional

# Common timestamp patterns
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-09-12T14:32:00Z
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "%Y-%m-%dT%H:%M:%SZ"),
    # ISO 8601 with offset: 2024-09-12T14:32:00+00:00
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", None),
    # Slack-style: [2024-09-12 14:31 UTC]
    (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "%Y-%m-%d %H:%M UTC"),
    # Syslog-style: Sep 12 14:32:00
    (r"[A-Z][a-z]{2} \d{1,2} \d{2}:\d{2}:\d{2}", None),
    # Date only: 2024-09-12
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
]


def extract_first_timestamp(text: str) -> Optional[str]:
    """Extract the first recognizable timestamp from text."""
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = re.search(pattern, text)
        if match:
            raw = match.group(0)
            if fmt:
                try:
                    dt = datetime.strptime(raw, fmt)
                    return dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    pass
            return raw
    return None


def truncate(text: str, max_chars: int = 12000) -> str:
    """Truncate text to max_chars, appending a note if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... truncated, {len(text) - max_chars} chars omitted ...]"


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return len(text) // 4
