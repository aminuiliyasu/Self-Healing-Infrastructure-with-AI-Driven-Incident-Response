import os
from dataclasses import dataclass

def _get_float(name: str, default: str) -> float:
    return float(os.environ.get(name, default))

def _get_int(name: str, default: str) -> int:
    return int(os.environ.get(name, default))

def _get_bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y")

@dataclass(frozen=True)
class Settings:
    prometheus_url: str
    poll_interval_seconds: int
    app_job: str
    error_rate_threshold: float
    request_timeout_seconds: float
    remediate: bool
    remediate_dry_run: bool
    scale_namespace: str
    scale_deployment: str
    scale_target_replicas: int
    scale_max_replicas: int
    remediate_cooldown_seconds: int

def load_settings() -> Settings:
    base = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
    return Settings(
        prometheus_url=base,
        poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", "15"),
        app_job=os.environ.get("APP_JOB", "self-healing-app"),
        error_rate_threshold=_get_float("ERROR_RATE_THRESHOLD", "0.05"),
        request_timeout_seconds=_get_float("REQUEST_TIMEOUT_SECONDS", "10"),
        remediate=_get_bool("REMEDIATE", False),
        remediate_dry_run=_get_bool("REMEDIATE_DRY_RUN", True),
        scale_namespace=os.environ.get("SCALE_NAMESPACE", "default"),
        scale_deployment=os.environ.get("SCALE_DEPLOYMENT", "self-healing-app"),
        scale_target_replicas=_get_int("SCALE_TARGET_REPLICAS", "3"),
        scale_max_replicas=_get_int("SCALE_MAX_REPLICAS", "5"),
        remediate_cooldown_seconds=_get_int("REMEDIATE_COOLDOWN_SECONDS", "120"),
    )