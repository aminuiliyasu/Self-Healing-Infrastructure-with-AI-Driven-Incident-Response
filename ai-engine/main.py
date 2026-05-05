from __future__ import annotations

import json
import time

from config import load_settings
from prometheus_client import query_instant
from rules import evaluate

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
            }
        ),
        flush=True,
    )

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