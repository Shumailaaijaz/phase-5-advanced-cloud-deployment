---
name: github-actions-cicd
description: Configure multi-stage GitHub Actions workflows for automated lint, test, build, push, and Helm-based deploy to cloud Kubernetes. Includes Docker caching, environment configs, smoke tests, and one-click rollback. Use when setting up CI/CD for Phase V cloud deployment.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# GitHub Actions CI/CD

## Purpose

Configure multi-stage GitHub Actions workflows for automated lint, test, build, push, and deploy of the Todo Chatbot to cloud Kubernetes. Includes Docker image caching, Helm-based deployment, environment-specific configs, and one-click rollback.

## Used by

- CI/CD Pipeline Agent (Agent 6)

## When to Use

- Creating the main CI/CD pipeline workflow
- Configuring Docker image builds with GitHub Actions cache
- Setting up Helm-based deployment to OKE/AKS/GKE
- Implementing one-click rollback via workflow_dispatch
- Configuring branch protection and environment rules
- Managing secrets via GitHub Secrets

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_cloud` | string | Yes | "oke", "aks", or "gke" |
| `registry` | string | Yes | Container registry (GHCR, Docker Hub) |
| `helm_chart_path` | string | Yes | Path to Helm chart |
| `environments` | list | Yes | Deployment environments |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| CI/CD workflow | YAML | `.github/workflows/ci-cd.yml` |
| Rollback workflow | YAML | `.github/workflows/rollback.yml` |
| Helm values | YAML | Per-environment overrides |
| Documentation | text | Required GitHub Secrets list |

## Procedure

### Step 1: Pipeline Stages

```
lint-and-test → build-and-push → deploy → verify
```

### Step 2: Lint and Test Job

```yaml
- ruff check . && ruff format --check .
- pytest --cov=. --cov-report=xml -q
```

### Step 3: Build and Push Job

```yaml
- uses: docker/build-push-action@v5
  with:
    tags: |
      ghcr.io/${{ env.IMAGE_PREFIX }}:${{ github.sha }}
      ghcr.io/${{ env.IMAGE_PREFIX }}:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Step 4: Deploy Job

```yaml
helm upgrade --install todo-chatbot ./charts/todo-app \
  --set backend.image.tag=${{ github.sha }} \
  --atomic --timeout 10m --wait
```

### Step 5: Rollback Workflow

```yaml
on:
  workflow_dispatch:
    inputs:
      revision:
        description: 'Helm revision (0 = previous)'
        default: '0'
```

## Quality Standards

- [ ] Pipeline runs in under 15 minutes total
- [ ] Docker images tagged with git SHA for traceability
- [ ] Build caching via `type=gha` — only rebuilds changed layers
- [ ] `--atomic` on Helm upgrade: auto-rollback on failure
- [ ] Zero-downtime rolling updates with readiness probes
- [ ] Rollback is one-click via workflow_dispatch
- [ ] All secrets via GitHub Secrets — never in workflow files
- [ ] Branch protection: main requires passing CI
