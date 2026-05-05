import os
from dataclasses import dataclass

def _get_float(name: str, default: str) -> float:
    return float(os.environ.get(name, default))

def _get_int(name: str, default: str) -> int:
    return int(os.environ.get(name, default))

@dataclass(frozen=True)
class Settings:
    prometheus_url: str
    poll_interval_seconds: int
    app_job: str
    error_rate_threshold: float
    request_timeout_seconds: float

def load_settings() -> Settings:
    base = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
    return Settings(
        prometheus_url=base,
        poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", "15"),
        app_job=os.environ.get("APP_JOB", "self-healing-app"),
        error_rate_threshold=_get_float("ERROR_RATE_THRESHOLD", "0.05"),
        request_timeout_seconds=_get_float("REQUEST_TIMEOUT_SECONDS", "10"),
    )