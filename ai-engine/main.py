from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from config import Settings, load_settings
from prometheus_api import query_instant
from rules import evaluate


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _maybe_run_scale_remediation(settings: Settings, last_run_ts: float) -> float:
    """Invoke automation/scale_deployment.sh for high_error_rate when REMEDIATE=1."""
    if not settings.remediate:
        return last_run_ts
    now = time.monotonic()
    if now - last_run_ts < settings.remediate_cooldown_seconds:
        return last_run_ts

    script = _repo_root() / "automation" / "scale_deployment.sh"
    env = os.environ.copy()
    env["NAMESPACE"] = settings.scale_namespace
    env["DEPLOYMENT"] = settings.scale_deployment
    env["TARGET_REPLICAS"] = str(settings.scale_target_replicas)
    env["MAX_REPLICAS"] = str(settings.scale_max_replicas)
    env["DRY_RUN"] = "true" if settings.remediate_dry_run else "false"

    proc = subprocess.run(
        ["/bin/bash", str(script)],
        env=env,
        capture_output=True,
        text=True,
    )
    print(
        json.dumps(
            {
                "type": "remediation_invoked",
                "detail": {
                    "script": str(script),
                    "dry_run": settings.remediate_dry_run,
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                },
            }
        ),
        flush=True,
    )
    return now


def main() -> None:
    settings = load_settings()

    error_query = (
        f'sum(rate(http_errors_total{{job="{settings.app_job}"}}[1m]))'
    )
    up_query = f'up{{job="{settings.app_job}"}}'

    print(
        json.dumps(
            {
                "event": "ai_engine_started",
                "prometheus_url": settings.prometheus_url,
                "poll_interval_seconds": settings.poll_interval_seconds,
                "remediate": settings.remediate,
                "remediate_dry_run": settings.remediate_dry_run,
            }
        ),
        flush=True,
    )

    last_remediate_ts = -settings.remediate_cooldown_seconds

    while True:
        try:
            err_rate = query_instant(
                settings.prometheus_url,
                error_query,
                settings.request_timeout_seconds,
            )
            up = query_instant(
                settings.prometheus_url,
                up_query,
                settings.request_timeout_seconds,
            )

            incidents = evaluate(
                error_rate_per_s=err_rate,
                up=up,
                error_threshold=settings.error_rate_threshold,
            )

            for inc in incidents:
                print(json.dumps(inc), flush=True)
                if settings.remediate and inc.get("type") == "high_error_rate":
                    last_remediate_ts = _maybe_run_scale_remediation(
                        settings, last_remediate_ts
                    )

        except Exception as e:
            print(
                json.dumps(
                    {
                        "type": "engine_error",
                        "severity": "critical",
                        "detail": {"error": str(e)},
                    }
                ),
                flush=True,
            )

        time.sleep(settings.poll_interval_seconds)

if __name__ == "__main__":
    main()