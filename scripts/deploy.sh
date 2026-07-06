#!/usr/bin/env bash
# Build the app image and deploy it to a namespace with kustomize.
# Usage: ./scripts/deploy.sh [dev|staging]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV="${1:-dev}"

if [[ "$ENV" != "dev" && "$ENV" != "staging" ]]; then
  echo "usage: $0 [dev|staging]" >&2
  exit 1
fi

docker build -t self-healing-app:latest "$ROOT/app"

# Minikube can't see local images unless we load them into the cluster.
if command -v minikube >/dev/null 2>&1 && minikube status >/dev/null 2>&1; then
  minikube image load self-healing-app:latest
fi

# Namespaces are normally created by Terraform; create one here as a fallback
# so the script also works on a fresh cluster.
kubectl get namespace "$ENV" >/dev/null 2>&1 || kubectl create namespace "$ENV"

kubectl apply -k "$ROOT/k8s/overlays/$ENV"
kubectl rollout status "deployment/self-healing-app" -n "$ENV"

echo "deployed to namespace: $ENV"
