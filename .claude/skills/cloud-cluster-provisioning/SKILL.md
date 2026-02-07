---
name: cloud-cluster-provisioning
description: Provision production-grade Kubernetes clusters on Oracle OKE (primary, always-free), Azure AKS, or Google Cloud GKE. Configure kubectl, install Dapr, set up ingress. Use when deploying the Todo Chatbot to cloud Kubernetes for Phase V Part C.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Cloud Cluster Provisioning

## Purpose

Provision production-grade Kubernetes clusters on Oracle OKE (primary, always-free), Azure AKS, or Google Cloud GKE. Configure kubectl access, install Dapr, and prepare the cluster for Helm-based deployment.

## Used by

- Cloud Deployment Agent (Agent 5)
- CI/CD Pipeline Agent (Agent 6)

## When to Use

- Creating an OKE cluster on Oracle Cloud always-free tier
- Setting up AKS on Azure with $200 credits
- Provisioning GKE on Google Cloud with $300 credits
- Installing Dapr on cloud Kubernetes
- Configuring ingress controllers for external access
- Adapting Helm values for cloud environment

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloud_provider` | string | Yes | "oke", "aks", or "gke" |
| `cluster_name` | string | Yes | Name for the K8s cluster |
| `node_config` | dict | Yes | Node size, count, machine type |
| `region` | string | Yes | Cloud region |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Creation commands | bash | Cloud CLI for cluster provisioning |
| kubectl config | bash | Commands to connect kubectl |
| Dapr installation | bash | Dapr init for cloud K8s |
| Ingress setup | bash | NGINX Ingress Controller |
| Cost estimate | text | Expected cost and free-tier limits |

## Procedure

### Oracle OKE (Recommended — Always Free)

```bash
oci ce cluster create --name todo-chatbot-cluster ...
oci ce node-pool create --node-shape VM.Standard.A1.Flex \
  --node-shape-config '{"ocpus": 2, "memoryInGBs": 12}' --size 2
oci ce cluster create-kubeconfig --cluster-id $CLUSTER_ID
```

### Azure AKS ($200 credit / 30 days)

```bash
az aks create --resource-group todo-rg --name todo-aks \
  --node-count 2 --node-vm-size Standard_B2s
az aks get-credentials --name todo-aks --resource-group todo-rg
```

### Google Cloud GKE ($300 credit / 90 days)

```bash
gcloud container clusters create todo-gke \
  --zone us-central1-a --num-nodes 2 --machine-type e2-medium
gcloud container clusters get-credentials todo-gke
```

### Common Post-Setup

```bash
dapr init -k --runtime-version 1.13.0
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
kubectl create namespace todo-app
```

## Quality Standards

- [ ] Oracle OKE preferred for cost (always-free, no charge after trial)
- [ ] Smallest viable node sizes to conserve credits
- [ ] `kubectl get nodes` shows Ready after creation
- [ ] Dapr installed with pinned version for reproducibility
- [ ] NGINX Ingress Controller deployed
- [ ] Credentials via cloud CLI auth — never in git
- [ ] Cluster creation includes preview/dry-run step
