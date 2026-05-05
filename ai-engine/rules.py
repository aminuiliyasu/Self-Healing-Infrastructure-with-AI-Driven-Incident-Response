from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def evaluate(
    *,
    error_rate_per_s: Optional[float],
    up: Optional[float],
    error_threshold: float,
) -> list[dict[str, Any]]:
    """
    error_rate_per_s: sum(rate(http_errors_total{job=...}[1m])) — errors per second (approx).
    up: up{job=...} — 1 means target healthy, 0 down, None if no data.
    """
    incidents: list[dict[str, Any]] = []

    if up is not None and up < 1:
        incidents.append(
            {
                "type": "target_down",
                "severity": "critical",
                "timestamp": _now_iso(),
                "detail": {"up": up},
            }
        )

    if error_rate_per_s is not None and error_rate_per_s > error_threshold:
        incidents.append(
            {
                "type": "high_error_rate",
                "severity": "warning",
                "timestamp": _now_iso(),
                "detail": {
                    "error_rate_per_s": error_rate_per_s,
                    "threshold": error_threshold,
                },
            }
        )

    return incidents