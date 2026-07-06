#!/usr/bin/env bash
# Fire requests at the app's /error endpoint so Prometheus sees a rising
# error rate and the engine opens an incident.
# Usage: ./scripts/inject_errors.sh http://<host>:<port> [count]
set -euo pipefail

BASE="${1:?need base URL, e.g. http://127.0.0.1:30051}"
COUNT="${2:-100}"

echo "sending $COUNT requests to $BASE/error ..."
for _ in $(seq 1 "$COUNT"); do
  curl -fsS "$BASE/error" >/dev/null 2>&1 || true
  sleep 0.2
done
echo "done"
