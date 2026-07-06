output "environments" {
  value = keys(local.environments)
}

output "app_namespaces" {
  value = { for k, v in kubernetes_namespace.app : k => v.metadata[0].name }
}

output "monitoring_namespace" {
  value = kubernetes_namespace.monitoring.metadata[0].name
}

output "prometheus_nodeport" {
  description = "Prometheus is exposed on this NodePort (see monitoring/prometheus-values.yaml)"
  value       = 30090
}

output "deploy_commands" {
  value = {
    dev     = "./scripts/deploy.sh dev"
    staging = "./scripts/deploy.sh staging"
  }
}
