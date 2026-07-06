variable "kubeconfig_path" {
  type        = string
  default     = "~/.kube/config"
  description = "Path to kubeconfig"
}

variable "kube_context" {
  type        = string
  default     = "minikube"
  description = "Kubeconfig context to use (e.g. minikube, kind-kind)"
}

variable "install_monitoring" {
  type        = bool
  default     = true
  description = "Install Prometheus into the monitoring namespace via Helm"
}
