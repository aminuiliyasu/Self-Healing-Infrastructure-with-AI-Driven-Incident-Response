"""Rule-based root-cause classification.

Each rule looks at the current telemetry (error rate, latency, target health)
and produces an incident with a root cause and a suggested remediation. The
engine decides whether to actually execute the remediation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _incident(inc_type: str, severity: str, root_cause: str, remediation: str, detail: dict) -> dict[str, Any]:
    return {
        "type": inc_type,
        "severity": severity,
        "timestamp": _now_iso(),
        "root_cause": root_cause,
        "remediation": remediation,
        "detail": detail,
    }


def evaluate(
    *,
    error_rate_per_s: Optional[float],
    up: Optional[float],
    latency_p95_s: Optional[float],
    error_threshold: float,
    latency_threshold_s: float,
) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []

    # Target not reachable at all -> restart it.
    if up is not None and up < 1:
        incidents.append(
            _incident(
                "target_down",
                "critical",
                "scrape_target_unreachable",
                "restart_deployment",
                {"up": up},
            )
        )

    errors_high = error_rate_per_s is not None and error_rate_per_s > error_threshold
    latency_high = latency_p95_s is not None and latency_p95_s > latency_threshold_s

    if errors_high:
        if latency_high:
            # Errors and latency rising together usually means the pods are
            # overloaded, so adding replicas is the right first move.
            root_cause = "overload_high_errors_and_latency"
            remediation = "scale_deployment"
        else:
            # Errors without a latency spike look like an application bug,
            # scaling would not help here.
            root_cause = "elevated_errors_low_latency"
            remediation = "investigate_logs"
        incidents.append(
            _incident(
                "high_error_rate",
                "warning",
                root_cause,
                remediation,
                {
                    "error_rate_per_s": error_rate_per_s,
                    "latency_p95_s": latency_p95_s,
                    "error_threshold": error_threshold,
                    "latency_threshold_s": latency_threshold_s,
                },
            )
        )
    elif latency_high:
        # Slow but not failing yet -> scale before it turns into errors.
        incidents.append(
            _incident(
                "high_latency",
                "warning",
                "latency_p95_above_threshold",
                "scale_deployment",
                {
                    "latency_p95_s": latency_p95_s,
                    "latency_threshold_s": latency_threshold_s,
                },
            )
        )

    return incidents
