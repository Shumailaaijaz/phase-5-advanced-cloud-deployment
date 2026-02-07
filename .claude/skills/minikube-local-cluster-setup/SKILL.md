---
name: minikube-local-cluster-setup
description: Reliably start a Minikube cluster with docker driver on Windows + WSL2 + Docker Desktop. Use when setting up a local Kubernetes cluster for Phase IV, starting or restarting Minikube, tuning WSL2 memory for Minikube, or verifying cluster health after setup. Also use when troubleshooting Minikube start failures like PROVIDER_DOCKER_NOT_RUNNING, signal killed, or OOM errors.
allowed-tools: Read, Write, Edit, Bash
---

# Minikube Local Cluster Setup

## Purpose

Provide a deterministic, copy-pasteable procedure to go from zero to a running Minikube cluster with docker driver on Windows + WSL2 + Docker Desktop. Covers prerequisite checks, .wslconfig tuning, clean start, and full verification.

## Used by

- minikube-docker-setup agent
- helm-chart-creator agent
- ai-devops-k8s agent

## Procedure

### Phase 0: Prerequisite Checks

Run these checks **before** attempting `minikube start`. Abort and fix any failure.

```powershell
# 1. Docker Desktop running? (PowerShell)
docker version
# Expect: Client AND Server sections. If Server missing → open Docker Desktop, wait 60s.

# 2. WSL2 is default?
wsl --status
# Expect: "Default Version: 2"

# 3. Docker Desktop WSL2 integration enabled?
# Manual check: Docker Desktop → Settings → Resources → WSL Integration → your distro toggled ON

# 4. minikube binary exists?
minikube version
# If missing → install:
# winget install Kubernetes.minikube   (PowerShell Admin)
# OR from WSL:
# curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
# sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 5. kubectl binary exists?
kubectl version --client
# If missing: Docker Desktop bundles it. Otherwise:
# winget install Kubernetes.kubectl   (PowerShell Admin)
```

### Phase 1: WSL2 Resource Tuning

Create or verify `C:\Users\<username>\.wslconfig`:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

After editing, restart WSL:

```powershell
wsl --shutdown
# Wait 5 seconds, then reopen WSL terminal
```

**Guidance:** If host has 8 GB RAM, use `memory=4GB`. If 16 GB+, use `memory=6GB`. Never allocate more than 50% of host RAM.

### Phase 2: Clean Old State (if needed)

Only run this when a previous cluster is broken, stuck, or you need a fresh start:

```powershell
minikube delete --all --purge
```

This removes all clusters, profiles, and cached images. Use sparingly.

### Phase 3: Start the Cluster

Preferred execution shell: **Windows PowerShell**.

```powershell
minikube start --driver=docker --memory=3072 --cpus=2 --kubernetes-version=stable
```

**From WSL Ubuntu** (alternative — only if user prefers):

```bash
minikube start --driver=docker --memory=3072 --cpus=2 --kubernetes-version=stable
```

Flags explained:
- `--driver=docker` — uses Docker Desktop as the VM driver (required for WSL2 path)
- `--memory=3072` — allocates 3 GB to the Minikube VM (safe for 4 GB WSL limit)
- `--cpus=2` — allocates 2 CPU cores
- `--kubernetes-version=stable` — pins to latest stable k8s release

### Phase 4: Verification

Run **all** of these. Every one must pass.

```powershell
# 1. Minikube status
minikube status
# Expect: host: Running, kubelet: Running, apiserver: Running, kubeconfig: Configured

# 2. Cluster info
kubectl cluster-info
# Expect: Kubernetes control plane is running at https://...

# 3. Node ready
kubectl get nodes
# Expect: STATUS = Ready

# 4. System pods running
kubectl get pods -A
# Expect: All pods Running or Completed (coredns, etcd, kube-apiserver, etc.)

# 5. Docker-Minikube integration
minikube docker-env
# Shows environment variables. To use minikube's Docker daemon:
# eval $(minikube docker-env)        # bash/zsh
# minikube docker-env | Invoke-Expression  # PowerShell
```

### Phase 5: Post-Setup Enablement

Enable commonly needed addons for the Todo Chatbot app:

```powershell
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

Verify addons:

```powershell
minikube addons list | findstr enabled
# WSL alternative:
minikube addons list | grep enabled
```

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `PROVIDER_DOCKER_NOT_RUNNING` | Docker Desktop not started or WSL integration off | Start Docker Desktop; enable WSL2 integration for distro |
| `signal: killed` | WSL2 OOM — insufficient memory | Edit `.wslconfig` to increase memory; `wsl --shutdown`; restart |
| `DRV_UNSUPPORTED_OS` | Wrong driver in WSL | Use `--driver=docker`, not `hyperv` or `none` |
| `kubectl: command not found` | kubectl not in PATH | `winget install Kubernetes.kubectl` or enable in Docker Desktop settings |
| Stuck at "Pulling base image" | Slow network or Docker rate limit | Wait; or `docker pull gcr.io/k8s-minikube/kicbase:v0.0.44` manually |
| Cluster hangs after start | Resource starvation | Reduce `--memory` and `--cpus`; check host resource usage |

## Output Format

After successful setup, report:

1. Minikube version installed
2. Kubernetes version running
3. Node status (Ready / NotReady)
4. System pod count and status summary
5. Enabled addons list
