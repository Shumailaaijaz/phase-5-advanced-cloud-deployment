---
name: cloud-secrets-management
description: Securely manage application secrets across Minikube and cloud using Dapr Secrets building block backed by Kubernetes Secrets, Azure Key Vault, or OCI Vault. Use when configuring secret storage and retrieval for Phase V deployments.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Cloud Secrets Management

## Purpose

Securely manage application secrets (DATABASE_URL, API keys, Kafka credentials, JWT secrets) across Minikube and cloud environments using Dapr Secrets building block backed by Kubernetes Secrets, Azure Key Vault, or OCI Vault.

## Used by

- Dapr Integration Agent (Agent 3)
- Cloud Deployment Agent (Agent 5)
- CI/CD Pipeline Agent (Agent 6)

## When to Use

- Setting up Kubernetes Secrets for Minikube deployment
- Configuring Azure Key Vault or OCI Vault for cloud secrets
- Creating Dapr secret store components
- Implementing application code to retrieve secrets via Dapr API
- Documenting secret rotation procedures
- Managing secrets in GitHub Actions

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `secret_store_type` | string | Yes | kubernetes, azure-keyvault, oci-vault |
| `secrets_list` | list | Yes | Secret key names to manage |
| `deployment_target` | string | Yes | "minikube" or "cloud" |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Dapr component | YAML | Secret store component definition |
| K8s Secret | YAML | Base Kubernetes Secret manifest |
| Cloud config | YAML/bash | Cloud vault setup commands |
| Python retrieval | Python | Application code for secret access |
| Rotation docs | text | Secret rotation procedure |

## Procedure

### Step 1: Kubernetes Secrets (Base Layer)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: todo-app-secrets
type: Opaque
data:
  database-url: {{ .Values.secrets.databaseUrl | b64enc }}
  better-auth-secret: {{ .Values.secrets.betterAuthSecret | b64enc }}
  openai-api-key: {{ .Values.secrets.openaiApiKey | b64enc }}
```

### Step 2: Dapr Secret Store Component

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-secrets
spec:
  type: secretstores.kubernetes  # or secretstores.azure.keyvault
  version: v1
```

### Step 3: Application Retrieval

```python
async def get_secret(key: str) -> str:
    if settings.USE_DAPR:
        secrets = await dapr_get_secret("taskflow-secrets", key)
        return secrets.get(key, "")
    else:
        return os.getenv(key.upper().replace("-", "_"), "")
```

### Step 4: GitHub Actions Secrets

Store in GitHub Settings > Secrets:
- `DATABASE_URL`, `BETTER_AUTH_SECRET`, `OPENAI_API_KEY`
- `KAFKA_BROKERS`, `KAFKA_USERNAME`, `KAFKA_PASSWORD`
- `KUBECONFIG` (cloud cluster access)

## Quality Standards

- [ ] Never store secrets in plain text in committed files
- [ ] Secrets via `--set` during helm install or sealed-secrets
- [ ] Dapr abstracts backend: swap K8s → Azure Key Vault with YAML only
- [ ] Application uses `get_secret()` — never `os.environ` for sensitive values
- [ ] Rotation documented for each secret without downtime
- [ ] RBAC: only todo-app service account reads todo-app-secrets
- [ ] GitHub Secrets for CI/CD — never in workflow YAML
