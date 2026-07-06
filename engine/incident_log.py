"""Append-only JSONL log of incidents, remediations and resolutions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def record_incident(self, incident: dict[str, Any]) -> None:
        self.write({"event": "incident", "at": _now_iso(), "incident": incident})

    def record_remediation(
        self,
        *,
        incident_type: str,
        action: str,
        started_at: str,
        finished_at: str,
        success: bool,
        detail: dict[str, Any],
    ) -> None:
        self.write(
            {
                "event": "remediation",
                "incident_type": incident_type,
                "action": action,
                "started_at": started_at,
                "finished_at": finished_at,
                "success": success,
                "detail": detail,
            }
        )

    def record_resolution(
        self,
        *,
        incident_type: str,
        opened_at: str,
        resolved_at: str,
        duration_seconds: float,
    ) -> None:
        self.write(
            {
                "event": "resolved",
                "incident_type": incident_type,
                "opened_at": opened_at,
                "resolved_at": resolved_at,
                "duration_seconds": duration_seconds,
            }
        )


def read_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize_log(path: Path) -> dict[str, Any]:
    """Aggregate the log into the numbers we care about (counts, MTTR)."""
    incidents = 0
    remediations = 0
    remediations_ok = 0
    recovery_times: list[float] = []

    for row in read_log(path):
        event = row.get("event")
        if event == "incident":
            incidents += 1
        elif event == "remediation":
            remediations += 1
            if row.get("success"):
                remediations_ok += 1
        elif event == "resolved":
            recovery_times.append(float(row["duration_seconds"]))

    auto_pct = (remediations_ok / incidents * 100) if incidents else 0.0
    mttr = (sum(recovery_times) / len(recovery_times)) if recovery_times else None
    return {
        "incidents": incidents,
        "remediations": remediations,
        "auto_resolved": remediations_ok,
        "auto_resolution_pct": round(auto_pct, 1),
        "resolved": len(recovery_times),
        "mttr_seconds": round(mttr, 1) if mttr is not None else None,
    }
