# Cloud Deployment Guide — Phase V

## Provider Comparison

| Provider | Values File | Free Tier | Ingress | Registry |
|----------|-------------|-----------|---------|----------|
| **Oracle OKE** (primary) | `values-cloud.yaml` | Always-free (4 OCPUs, 24GB) | NGINX | GHCR |
| **Azure AKS** (fallback) | `values-aks.yaml` | $200/30 days | App Gateway | ACR |
| **Google GKE** (fallback) | `values-gke.yaml` | $300/90 days | GCE | GCR |

## Quick Deploy (any provider)

```bash
# 1. Set secrets
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."
export BETTER_AUTH_SECRET="your-secret"

# 2. Deploy with Helm
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-cloud.yaml \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  --set backend.secrets.openaiApiKey="$OPENAI_API_KEY" \
  --set backend.secrets.betterAuthSecret="$BETTER_AUTH_SECRET" \
  --namespace todo-app --create-namespace --atomic --timeout 10m
```

## AKS-specific

```bash
# Use values-aks.yaml instead
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-aks.yaml \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  ...
```

## GKE-specific

```bash
# Use values-gke.yaml instead
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-gke.yaml \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  ...
```

## Rollback

```bash
# List revisions
helm history todo-app -n todo-app

# Rollback to previous
helm rollback todo-app 1 -n todo-app --wait
```

## Verify Deployment

```bash
# Check all pods running
kubectl get pods -n todo-app

# Check Dapr sidecars (2/2 containers per pod)
kubectl get pods -n todo-app -o wide

# Test backend health
kubectl port-forward svc/todo-app-backend 8000:8000 -n todo-app
curl http://localhost:8000/health
```
