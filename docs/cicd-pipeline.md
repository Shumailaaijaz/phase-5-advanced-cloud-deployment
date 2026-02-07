# CI/CD Pipeline — Phase V

## Pipeline Overview

GitHub Actions workflow at `.github/workflows/deploy.yml`:

```
Push to main → Lint & Test → Build & Push (GHCR) → Deploy (Helm)
```

## Stages

| Stage | Tools | What it does |
|-------|-------|-------------|
| **Lint** | ruff check, ruff format | Python code quality |
| **Test** | pytest --cov | Unit tests + coverage |
| **Build** | Docker Buildx | Multi-stage image build |
| **Push** | GHCR | Push to ghcr.io/shumaila/todo-{backend,frontend} |
| **Deploy** | Helm upgrade | Deploy to K8s cluster (when KUBECONFIG configured) |

## Rollback Workflow

Manual trigger at `.github/workflows/rollback.yml`:

```
workflow_dispatch (revision input) → helm rollback todo-app {revision}
```

## Triggering the Pipeline

```bash
# Any push to main triggers the full pipeline
git push origin main

# Manual rollback via GitHub Actions UI
# Go to Actions → Rollback → Run workflow → Enter revision number
```

## Required Secrets

| Secret | Where | Purpose |
|--------|-------|---------|
| `GITHUB_TOKEN` | Auto-provided | GHCR push |
| `KUBECONFIG` | Repo settings | K8s cluster access (optional) |

## Expected Pipeline Duration

Target: < 15 minutes total (lint 1m, test 2m, build 5m, push 2m, deploy 3m)
