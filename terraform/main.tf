# Provisions the cluster-side pieces this project needs:
#   - one namespace per app environment (dev, staging)
#   - a monitoring namespace with Prometheus installed via Helm
#
# Works against any cluster the kubeconfig points at (Minikube locally).
# The app itself is deployed with kustomize (k8s/overlays), not Terraform.

terraform {
  required_version = ">= 1.5"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
  }
}

provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kube_context
  }
}

locals {
  environments = {
    dev     = { replicas = 1 }
    staging = { replicas = 2 }
  }
}

resource "kubernetes_namespace" "app" {
  for_each = local.environments

  metadata {
    name = each.key
    labels = {
      project     = "self-healing-infra"
      environment = each.key
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      project = "self-healing-infra"
    }
  }
}

resource "helm_release" "prometheus" {
  count = var.install_monitoring ? 1 : 0

  name       = "monitoring"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [file("${path.module}/../monitoring/prometheus-values.yaml")]
}
