from __future__ import annotations

from typing import Any, Optional

import requests


class PrometheusApiError(RuntimeError):
    pass


def query_instant(prometheus_base_url: str, promql: str, timeout: float) -> Optional[float]:
    url = f"{prometheus_base_url}/api/v1/query"
    resp = requests.get(
        url,
        params={"query": promql},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload: dict[str, Any] = resp.json()

    if payload.get("status") != "success":
        raise PrometheusApiError(f"Unexpected Prometheus response: {payload}")

    result = payload.get("data", {}).get("result") or []
    if not result:
        return None

    _ts, value_str = result[0]["value"]
    return float(value_str)
