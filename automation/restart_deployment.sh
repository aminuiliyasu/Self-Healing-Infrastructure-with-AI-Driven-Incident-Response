#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-dev}"
DEPLOYMENT="${DEPLOYMENT:-self-healing-app}"
DRY_RUN="${DRY_RUN:-true}"

CMD=(kubectl rollout restart "deployment/${DEPLOYMENT}" -n "${NAMESPACE}")

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "[dry-run] would run: ${CMD[*]}"
  exit 0
fi

exec "${CMD[@]}"
