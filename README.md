# Self-Healing Infrastructure with AI-Driven Incident Response

[GitHub repository](https://github.com/aminuiliyasu/Self-Healing-Infrastructure-with-AI-Driven-Incident-Response)

## Project summary

Built an autonomous infrastructure monitoring platform using Prometheus and Python to detect anomalies and trigger automated remediation workflows in real time.

Developed a rule-based incident analysis engine that identified root causes from telemetry and executed corrective actions through Kubernetes and Bash automation.

Improved operational efficiency and reduced incident response time through automated detection and self-healing workflows.

Technologies: Python, Kubernetes, Prometheus, Terraform, Docker.

## Overview

This project demonstrates a self-healing infrastructure platform that can detect, analyze, and remediate production incidents with minimal human intervention.

Traditional monitoring systems only alert engineers when something breaks. This system goes further by identifying anomalies, inferring likely root causes, and applying corrective actions in near real time.

The primary goals are to reduce downtime, improve reliability, and lower operational overhead.

---

## Key Features

- Real-time monitoring of core service metrics (requests, latency, errors) via Prometheus
- Rule-based incident signals from telemetry (extensible toward richer ML later)
- Automated remediation hooks (scale deployment via script + optional ai-engine integration)
- Kubernetes deployment of the sample workload
- Grafana dashboards wired to Prometheus
- CI validation: Docker image build + smoke test; Terraform `validate` (no cloud apply)

---

## Tech Stack

| Layer | Tools |
|--------|--------|
| App | Python, Flask, `prometheus_client` |
| Containers | Docker |
| Orchestration | Kubernetes (Minikube / Kind / cloud) |
| Metrics | Prometheus (Helm chart in demo) |
| Dashboards | Grafana (Helm chart in demo) |
| Analysis | Python ai-engine (Prometheus HTTP API + rules) |
| Automation | Bash + `kubectl` |
| CI/CD | GitHub Actions |
| IaC docs | Terraform stub + `terraform/README.md` (local cluster first; cloud module optional) |

---

## System Architecture

The platform is organized into four main layers:

1. **Monitoring Layer** — Prometheus scrapes the sample app (`/metrics`) and cluster metrics.
2. **Logging Layer** — ELK is listed as a future/extension path; the demo focuses on metrics-first.
3. **Analysis Engine** (`ai-engine/`) — Polls Prometheus, evaluates rules, emits JSON incidents; optional remediation hook.
4. **Automation Engine** (`automation/`) — Scales deployments via `kubectl` with dry-run and replica caps.

---

## Workflow

1. Metrics are scraped from the running service (Prometheus).
2. The analysis engine evaluates PromQL-derived signals on an interval.
3. When abnormal behavior is detected, rules classify an incident type (e.g. `high_error_rate`).
4. Optionally, remediation runs (`automation/scale_deployment.sh`) with **dry-run by default**.
5. Events are visible in logs (JSON lines) and in Grafana for metrics.

**Remediation (demo):** On sustained high error rate the rules emit a `high_error_rate` incident. Use `automation/scale_deployment.sh` (`DRY_RUN`, `MAX_REPLICAS`). Set `REMEDIATE=1` so ai-engine invokes that script when a `high_error_rate` incident fires (throttled by `REMEDIATE_COOLDOWN_SECONDS`). Default **`REMEDIATE_DRY_RUN=true`** only prints the `kubectl scale` command; set **`REMEDIATE_DRY_RUN=false`** for a real scale. Replica caps: `MAX_REPLICAS` in the script or `SCALE_MAX_REPLICAS` when invoked from the engine.

---

## Example Incident Flow

**Scenario:** Elevated HTTP errors on the sample app.

- Prometheus records `http_errors_total` and rates increase.
- ai-engine crosses the error-rate threshold → `high_error_rate` incident JSON.
- Operator or automation scales the Deployment (dry-run or real, per env).
- Request/error metrics stabilize as replicas absorb load (demo assumption).

---

## Prerequisites

- **Docker** — build and run the app image
- **Kubernetes** — Minikube or Kind recommended for local demos (`kubectl` configured)
- **Python 3.10+** — ai-engine and local app run
- **Helm** — optional but used below for Prometheus/Grafana install

---

## Running the sample application

### Option A — Local (fastest for code changes)

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Endpoints: `http://localhost:5000/` · `/health` · `/metrics`

If port **5000** is busy: `python3 -c "from app import app; app.run(host='0.0.0.0', port=5001)"`

### Option B — Docker

From the **repository root**:

```bash
docker build -t self-healing-app ./app
docker run --rm -p 5002:5000 self-healing-app
```

Open `http://localhost:5002/health`

### Option C — Kubernetes (Minikube)

```bash
docker build -t self-healing-app:latest ./app
minikube image load self-healing-app:latest   # so the cluster can use your local image

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/self-healing-app -n default

minikube service self-healing-app --url
```

Use the printed URL for `/health` and `/metrics`.

---

## Observability (Prometheus + Grafana)

Prometheus and Grafana are installed with **Helm** (not plain `kubectl apply` on `monitoring/`). Example:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/prometheus \
  --namespace monitoring --create-namespace \
  --set server.service.type=NodePort \
  --set server.service.nodePort=30090

# Add scrape config for the sample app (after deploy + Service exist)
helm upgrade monitoring prometheus-community/prometheus \
  --namespace monitoring --reuse-values \
  -f monitoring/prometheus-extra-scrape.yaml
```

Install Grafana similarly (see your cluster notes); set the Prometheus datasource URL inside the cluster to:

`http://monitoring-prometheus-server.monitoring.svc.cluster.local`

Expose UIs with `minikube service -n monitoring … --url` as needed.

---

## Analysis engine (`ai-engine/`)

From repo root (or `cd ai-engine` and adjust imports / run `python main.py`):

```bash
cd ai-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export PROMETHEUS_URL=http://<minikube-ip>:30090   # Prometheus NodePort on host
export APP_JOB=self-healing-app
export REMEDIATE=0                                  # set to 1 to invoke automation hook
export REMEDIATE_DRY_RUN=true                       # false to allow real kubectl scale from engine

python3 main.py
```

Useful variables: `POLL_INTERVAL_SECONDS`, `ERROR_RATE_THRESHOLD`, `SCALE_NAMESPACE`, `SCALE_DEPLOYMENT`, `SCALE_TARGET_REPLICAS`, `SCALE_MAX_REPLICAS`, `REMEDIATE_COOLDOWN_SECONDS`.

---

## Automation (`automation/`)

```bash
chmod +x automation/scale_deployment.sh
DRY_RUN=true NAMESPACE=default DEPLOYMENT=self-healing-app TARGET_REPLICAS=3 ./automation/scale_deployment.sh
```

Set `DRY_RUN=false` only when your kube context is correct and you accept scaling.

---

## CI/CD

On push or pull request to **`main`** / **`master`**, GitHub Actions:

1. Builds `docker build ./app` and smoke-tests `/health` and `/metrics`.
2. Runs `terraform fmt -check`, `terraform init -backend=false`, and `terraform validate` in `terraform/` (no cloud resources created).

---

## Infrastructure as code (Terraform)

Local development targets **Minikube or Kind**; no cloud credentials are required to use this repo. See **`terraform/README.md`** for production-oriented notes. The root **`terraform/main.tf`** exists for CI validation and documentation—not to provision a cloud cluster by default.

---

## Project Structure

```text
├── app/                  # Flask sample app + Dockerfile
├── ai-engine/            # Prometheus polling + rules + optional remediation hook
├── automation/           # kubectl scale script (dry-run safe)
├── k8s/                  # Deployment + Service for the app
├── monitoring/           # Helm values snippets (e.g. extra Prometheus scrape config)
├── terraform/            # Minimal TF + README (scope / CI validate)
└── .github/workflows/    # CI
```

---

## Current Limitations

- Rule-based signals; ML is intentionally minimal / future work.
- Logging stack (ELK) not wired in the default path.
- Terraform does not create cloud clusters in CI or by default.

---

## Future Improvements

- Richer anomaly detection and incident deduplication
- Log correlation (Loki or ELK) and tracing
- GitOps (Argo CD / Flux) for manifests
- External alerting (PagerDuty, Slack)
- Optional cloud Terraform module for GKE/EKS/AKS (separate secrets / workspace)

---

## Why This Project

- Designing and operating distributed systems
- Combining observability with safe automation
- Clear boundaries: metrics → decisions → optional remediation

---

## License

MIT License
