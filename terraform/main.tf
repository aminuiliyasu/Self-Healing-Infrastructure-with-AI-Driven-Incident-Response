# Local development uses Minikube or Kind — clusters are not created here.
# Production would target a cloud provider; keep credentials and modules separate.

terraform {
  required_version = ">= 1.5"
}

output "development_note" {
  description = "How this repo treats infrastructure scope."
  value       = "Development: Minikube/Kind + kubectl apply. Production: add your cloud provider module (GKE/EKS/AKS) and workspaces — see README in this directory."
}
