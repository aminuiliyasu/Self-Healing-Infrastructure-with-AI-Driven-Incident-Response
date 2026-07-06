"""Simple web dashboard for the self-healing engine.

Shows live metrics from Prometheus and the incident/remediation history the
engine writes to data/incidents.jsonl. Read-only, one page, refreshes itself.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, render_template

# Reuse the engine's log reader instead of duplicating it.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "engine"))
from incident_log import read_log, summarize_log  # noqa: E402

app = Flask(__name__)

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
APP_JOB = os.environ.get("APP_JOB", "self-healing-app-dev")
LOG_PATH = Path(os.environ.get("INCIDENT_LOG_PATH", REPO_ROOT / "data" / "incidents.jsonl"))


def prom_query(promql: str):
    """Instant query; returns a float or None (no data / Prometheus down)."""
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql}, timeout=5
        )
        resp.raise_for_status()
        result = resp.json().get("data", {}).get("result") or []
        if not result:
            return None
        return float(result[0]["value"][1])
    except requests.RequestException:
        return None


def live_metrics() -> dict:
    up = prom_query(f'up{{job="{APP_JOB}"}}')
    err_rate = prom_query(f'sum(rate(http_errors_total{{job="{APP_JOB}"}}[1m]))')
    req_rate = prom_query(f'sum(rate(http_requests_total{{job="{APP_JOB}"}}[1m]))')
    latency = prom_query(
        "histogram_quantile(0.95, sum(rate("
        f'http_request_duration_seconds_bucket{{job="{APP_JOB}"}}[5m])) by (le))'
    )
    return {
        "up": up,
        "error_rate": err_rate,
        "request_rate": req_rate,
        "latency_p95": latency,
    }


def short_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return iso or "-"


@app.route("/")
def index():
    rows = read_log(LOG_PATH)
    incidents = [r for r in rows if r.get("event") == "incident"][-15:]
    remediations = [r for r in rows if r.get("event") == "remediation"][-15:]
    resolutions = [r for r in rows if r.get("event") == "resolved"][-15:]

    return render_template(
        "index.html",
        metrics=live_metrics(),
        summary=summarize_log(LOG_PATH),
        incidents=list(reversed(incidents)),
        remediations=list(reversed(remediations)),
        resolutions=list(reversed(resolutions)),
        app_job=APP_JOB,
        prometheus_url=PROMETHEUS_URL,
        short_time=short_time,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
