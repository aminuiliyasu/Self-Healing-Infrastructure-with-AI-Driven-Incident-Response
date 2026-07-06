# Terraform

This module sets up the cluster-side pieces the project needs:

- `dev` and `staging` namespaces for the app
- a `monitoring` namespace with Prometheus installed through the Helm provider

It works against whatever cluster your kubeconfig points at. Locally that is
Minikube; the same module would run against a managed cluster (EKS/GKE/AKS)
by changing `kube_context` — creating the cluster itself is out of scope here
and would live in its own root module.

## Usage

```bash
cd terraform
terraform init
terraform apply
```

Useful variables (see `variables.tf`):

- `kube_context` — defaults to `minikube`, set to `kind-kind` for Kind
- `install_monitoring` — set to `false` if you install Prometheus yourself

After apply, Prometheus is reachable on NodePort 30090:

```bash
minikube service -n monitoring monitoring-prometheus-server --url
```

The application itself is deployed with kustomize (`./scripts/deploy.sh dev`),
not Terraform — infra and app releases are deliberately kept separate.

CI runs `terraform fmt -check`, `init -backend=false` and `validate` only, so
no cluster or credentials are needed to keep the pipeline green.
