"""Small security primitives shared by adapters and operational logging."""

import re
from collections.abc import Mapping
from typing import Any

_SENSITIVE_KEY = re.compile(r"(authorization|api[_-]?key|secret|password|token|connection[_-]?string)", re.I)
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")
_AZURE_KEY = re.compile(r"(?i)(api-key\s*[:=]\s*)[^\s,;]+")


def redact(value: Any) -> Any:
    """Return a log-safe copy without mutating caller data."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else redact(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        return _AZURE_KEY.sub(r"\1[REDACTED]", _BEARER.sub("Bearer [REDACTED]", value))
    return value
