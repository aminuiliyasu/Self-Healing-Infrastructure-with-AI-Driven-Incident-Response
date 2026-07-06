#!/usr/bin/env bash
set -euo pipefail

# Required
NAMESPACE="${NAMESPACE:-dev}"
DEPLOYMENT="${DEPLOYMENT:-self-healing-app}"
TARGET_REPLICAS="${TARGET_REPLICAS:-3}"

# Safety
DRY_RUN="${DRY_RUN:-true}"          # true = only print kubectl command
MAX_REPLICAS="${MAX_REPLICAS:-5}"

if ! [[ "$TARGET_REPLICAS" =~ ^[0-9]+$ ]]; then
  echo "TARGET_REPLICAS must be an integer" >&2
  exit 1
fi

if (( TARGET_REPLICAS > MAX_REPLICAS )); then
  echo "Refusing to scale above MAX_REPLICAS=$MAX_REPLICAS (requested $TARGET_REPLICAS)" >&2
  exit 2
fi

CMD=(kubectl scale "deployment/${DEPLOYMENT}" -n "${NAMESPACE}" --replicas="${TARGET_REPLICAS}")

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "[dry-run] would run: ${CMD[*]}"
  exit 0
fi

exec "${CMD[@]}"