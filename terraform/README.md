# Terraform scope (honest)

This repository is built and tested primarily against a **local Kubernetes cluster** (Minikube or Kind). Manifests under `k8s/` and Helm-installed observability are applied with **`kubectl`** / **Helm**, not by Terraform in CI.

## Development

- Bring up Minikube (or Kind), build the image (`docker build -t self-healing-app ./app`), load it into the cluster if needed (`minikube image load …`), then apply YAML.

## Production-shaped setups

For GKE, EKS, or AKS you would typically:

1. Use a separate Terraform root module (often another repo) that creates the cluster, node pools, IAM/networking, and registry access.
2. Keep application manifests GitOps-style (Argo CD / Flux) or pipeline-delivered (`kubectl`, Helm upgrades).

The `main.tf` here only validates in CI and documents that separation—it **does not provision cloud resources** so this project stays clone-and-run friendly without cloud credentials.


