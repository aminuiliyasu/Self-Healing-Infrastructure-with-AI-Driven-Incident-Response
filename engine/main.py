"""Monitoring loop: poll Prometheus, evaluate rules, run remediation scripts.

Incidents are tracked as open/resolved so the log contains one record per
incident instead of one per poll. Time-to-recover is measured from the moment
an incident opens until its condition clears.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from config import Settings, load_settings
from incident_log import IncidentLog
from prometheus_api import query_instant
from rules import evaluate

REPO_ROOT = Path(__file__).resolve().parent.parent

# Remediation actions the engine is allowed to execute.
ACTION_SCRIPTS = {
    "scale_deployment": "scale_deployment.sh",
    "restart_deployment": "restart_deployment.sh",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_line(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def run_action(action: str, settings: Settings) -> subprocess.CompletedProcess[str]:
    script = REPO_ROOT / "automation" / ACTION_SCRIPTS[action]
    env = os.environ.copy()
    env["NAMESPACE"] = settings.scale_namespace
    env["DEPLOYMENT"] = settings.scale_deployment
    env["DRY_RUN"] = "true" if settings.remediate_dry_run else "false"
    if action == "scale_deployment":
        env["TARGET_REPLICAS"] = str(settings.scale_target_replicas)
        env["MAX_REPLICAS"] = str(settings.scale_max_replicas)
    return subprocess.run(["/bin/bash", str(script)], env=env, capture_output=True, text=True)


def maybe_remediate(
    incident: dict,
    settings: Settings,
    log: IncidentLog,
    last_run: dict[str, float],
) -> None:
    """Run the remediation suggested by the rules, respecting the cooldown."""
    action = incident.get("remediation")
    if not settings.remediate or action not in ACTION_SCRIPTS:
        return

    now = time.monotonic()
    if now - last_run.get(action, float("-inf")) < settings.remediate_cooldown_seconds:
        return
    last_run[action] = now

    started_at = now_iso()
    proc = run_action(action, settings)
    log.record_remediation(
        incident_type=incident["type"],
        action=action,
        started_at=started_at,
        finished_at=now_iso(),
        success=proc.returncode == 0,
        detail={
            "dry_run": settings.remediate_dry_run,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        },
    )
    log_line(
        {
            "event": "remediation",
            "action": action,
            "dry_run": settings.remediate_dry_run,
            "exit_code": proc.returncode,
        }
    )


def poll_once(
    settings: Settings,
    log: IncidentLog,
    active: dict[str, dict],
    last_run: dict[str, float],
) -> None:
    error_query = f'sum(rate(http_errors_total{{job="{settings.app_job}"}}[1m]))'
    up_query = f'up{{job="{settings.app_job}"}}'
    latency_query = (
        "histogram_quantile(0.95, sum(rate("
        f'http_request_duration_seconds_bucket{{job="{settings.app_job}"}}[5m])) by (le))'
    )

    err_rate = query_instant(settings.prometheus_url, error_query, settings.request_timeout_seconds)
    up = query_instant(settings.prometheus_url, up_query, settings.request_timeout_seconds)
    latency_p95 = query_instant(settings.prometheus_url, latency_query, settings.request_timeout_seconds)

    incidents = evaluate(
        error_rate_per_s=err_rate,
        up=up,
        latency_p95_s=latency_p95,
        error_threshold=settings.error_rate_threshold,
        latency_threshold_s=settings.latency_p95_threshold_s,
    )
    fired = {inc["type"] for inc in incidents}

    # New incidents: log once and (optionally) remediate.
    for inc in incidents:
        if inc["type"] in active:
            continue
        active[inc["type"]] = {"opened_at": inc["timestamp"], "opened_mono": time.monotonic()}
        log.record_incident(inc)
        log_line({"event": "incident_opened", **inc})
        maybe_remediate(inc, settings, log, last_run)

    # Incidents whose condition cleared: mark resolved with recovery time.
    for inc_type in list(active):
        if inc_type in fired:
            continue
        opened = active.pop(inc_type)
        duration = round(time.monotonic() - opened["opened_mono"], 1)
        log.record_resolution(
            incident_type=inc_type,
            opened_at=opened["opened_at"],
            resolved_at=now_iso(),
            duration_seconds=duration,
        )
        log_line({"event": "incident_resolved", "type": inc_type, "duration_seconds": duration})


def main() -> None:
    settings = load_settings()
    log = IncidentLog(Path(settings.incident_log_path))
    log_line(
        {
            "event": "engine_started",
            "prometheus_url": settings.prometheus_url,
            "app_job": settings.app_job,
            "remediate": settings.remediate,
            "remediate_dry_run": settings.remediate_dry_run,
        }
    )

    active: dict[str, dict] = {}
    last_run: dict[str, float] = {}

    while True:
        try:
            poll_once(settings, log, active, last_run)
        except Exception as e:  # noqa: BLE001 - keep the loop alive on Prometheus hiccups
            log_line({"event": "engine_error", "error": str(e)})
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
