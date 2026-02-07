---
name: helm-chart-generation
description: Create standard Helm 3.x charts for the Phase III Todo Chatbot application (frontend, backend, MCP server) targeting local Minikube deployment. Use when generating Chart.yaml, values.yaml, deployment/service/ingress/configmap/secret templates, or providing helm install/upgrade commands. Also use when adding new services to an existing chart, configuring environment variables or secrets via Helm, or troubleshooting helm template rendering errors.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Helm Chart Generation

## Purpose

Generate complete, idempotent Helm 3.x charts for the Todo Chatbot three-tier stack (frontend, backend, MCP server) with sane defaults for local Minikube deployment. Charts must render cleanly with `helm template`, never hardcode secrets, and include probes and resource limits on every container.

## Used by

- helm-chart-creator agent
- ai-devops-k8s agent
- minikube-docker-setup agent (for verification)

## Procedure

### Step 1: Gather Inputs

Confirm these before generating:

| Input | Example | Required |
|-------|---------|----------|
| Components | frontend, backend, mcp-server | Yes |
| Container images & tags | `todo-backend:latest` | Yes (or use placeholders) |
| Exposed ports | 3000, 8000, 8001 | Yes |
| Environment variables | DATABASE_URL, OPENAI_API_KEY | Yes |
| Persistence | External Neon or local PVC | Yes |
| Namespace | `todo-app` | Default provided |

If any input is missing, ask 2-3 targeted questions before proceeding.

### Step 2: Scaffold Chart Structure

Generate this directory tree:

```
todo-chatbot/
├── Chart.yaml
├── values.yaml
├── .helmignore
├── templates/
│   ├── _helpers.tpl
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── mcp-deployment.yaml
│   ├── mcp-service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── NOTES.txt
│   └── tests/
│       └── test-connection.yaml
└── charts/
```

Use separate template files per service for clarity.

### Step 3: Write Chart.yaml

```yaml
apiVersion: v2
name: todo-chatbot
description: Helm chart for Todo Chatbot (frontend + backend + MCP server)
type: application
version: 0.1.0
appVersion: "1.0.0"
keywords:
  - todo
  - chatbot
  - fastapi
  - nextjs
  - mcp
```

### Step 4: Write values.yaml

Structure all values under per-service keys. Follow these rules:
- Secrets get empty-string defaults with `# REQUIRED` comments
- Non-sensitive config gets reasonable defaults
- Every entry has an inline comment

```yaml
# -- Global settings
global:
  namespace: todo-app        # Target namespace

# -- Backend (FastAPI)
backend:
  replicaCount: 1
  image:
    repository: todo-backend
    tag: latest
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  probes:
    liveness:
      path: /health
      initialDelaySeconds: 10
      periodSeconds: 15
    readiness:
      path: /health
      initialDelaySeconds: 5
      periodSeconds: 10
  env:
    DATABASE_URL: ""           # REQUIRED — Neon PostgreSQL connection string
    BETTER_AUTH_SECRET: ""     # REQUIRED — JWT signing secret
  config:
    ENV: production
    LOG_LEVEL: info

# -- Frontend (Next.js)
frontend:
  replicaCount: 1
  image:
    repository: todo-frontend
    tag: latest
    pullPolicy: IfNotPresent
  service:
    type: NodePort             # NodePort for Minikube access
    port: 3000
    nodePort: 30080
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  probes:
    liveness:
      path: /
      initialDelaySeconds: 10
      periodSeconds: 15
    readiness:
      path: /
      initialDelaySeconds: 5
      periodSeconds: 10
  env:
    NEXT_PUBLIC_API_URL: "http://backend:8000"

# -- MCP Server
mcp:
  replicaCount: 1
  image:
    repository: todo-mcp
    tag: latest
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 8001
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  probes:
    liveness:
      path: /health/ready
      initialDelaySeconds: 10
      periodSeconds: 15
    readiness:
      path: /health/ready
      initialDelaySeconds: 5
      periodSeconds: 10
  env:
    DATABASE_URL: ""           # REQUIRED — same Neon connection string
    BETTER_AUTH_SECRET: ""     # REQUIRED — same JWT secret
    MCP_API_KEY: ""            # REQUIRED — server-to-server auth key

# -- Ingress (disabled by default for local dev)
ingress:
  enabled: false
  className: nginx
  hosts:
    - host: todo.local
      paths:
        - path: /
          service: frontend
        - path: /api
          service: backend
        - path: /mcp
          service: mcp
  tls: []

# -- Persistence (optional local PostgreSQL)
persistence:
  enabled: false               # Use external Neon by default
  storageClass: standard       # Minikube default
  size: 1Gi
  accessMode: ReadWriteOnce
```

### Step 5: Write _helpers.tpl

Include these named templates:

- `todo-chatbot.name` — chart name, truncated to 63 chars
- `todo-chatbot.fullname` — release + chart name, truncated to 63 chars
- `todo-chatbot.chart` — chart name + version
- `todo-chatbot.labels` — common Helm labels block
- `todo-chatbot.selectorLabels` — immutable selector labels only

### Step 6: Write Deployment Templates

For **each** service (backend, frontend, mcp), generate a deployment with:

1. Standard labels from `_helpers.tpl` (append component label: `app.kubernetes.io/component: backend`)
2. Matching `selector.matchLabels`
3. Container spec with:
   - Image from values (`{{ .Values.<svc>.image.repository }}:{{ .Values.<svc>.image.tag }}`)
   - `imagePullPolicy` from values
   - `containerPort` matching service port
   - `livenessProbe` and `readinessProbe` (httpGet on configured path/port)
   - `resources` from values
   - `env` entries: secrets via `secretKeyRef`, config via `configMapKeyRef`

### Step 7: Write Service Templates

For each service:
- `type` from values (ClusterIP / NodePort)
- Named port with protocol TCP
- Selector matching deployment labels

### Step 8: Write Secret and ConfigMap

**Secret** (`secret.yaml`):
- Contains all `env` entries marked REQUIRED in values.yaml
- Data values base64-encoded via `{{ .Values.<svc>.env.<KEY> | b64enc }}`

**ConfigMap** (`configmap.yaml`):
- Contains all `config` entries from values.yaml
- Plain string data

### Step 9: Write NOTES.txt

Post-install output must include:
- Pod status check command
- Access instructions (minikube service / port-forward)
- Log viewing commands
- Upgrade command reminder

### Step 10: Validate

Run before presenting to user:

```bash
# Lint the chart
helm lint ./todo-chatbot

# Dry-run render
helm template todo-chatbot ./todo-chatbot --namespace todo-app --debug

# Verify no unresolved placeholders (outside Go template syntax)
helm template todo-chatbot ./todo-chatbot | grep -E '\{\{[^}]+\}\}'
# Should return no output
```

### Step 11: Provide Install Commands

```bash
# Create namespace
kubectl create namespace todo-app --dry-run=client -o yaml | kubectl apply -f -

# Dry-run install (verify first)
helm install todo-chatbot ./todo-chatbot \
  --namespace todo-app \
  --set backend.env.DATABASE_URL="postgresql://user:pass@host/db" \
  --set backend.env.BETTER_AUTH_SECRET="your-secret" \
  --set mcp.env.DATABASE_URL="postgresql://user:pass@host/db" \
  --set mcp.env.BETTER_AUTH_SECRET="your-secret" \
  --set mcp.env.MCP_API_KEY="your-api-key" \
  --dry-run --debug

# Actual install
helm install todo-chatbot ./todo-chatbot \
  --namespace todo-app \
  --set backend.env.DATABASE_URL="postgresql://user:pass@host/db" \
  --set backend.env.BETTER_AUTH_SECRET="your-secret" \
  --set mcp.env.DATABASE_URL="postgresql://user:pass@host/db" \
  --set mcp.env.BETTER_AUTH_SECRET="your-secret" \
  --set mcp.env.MCP_API_KEY="your-api-key" \
  --atomic --timeout 5m

# Verify
kubectl get pods -n todo-app
kubectl get svc -n todo-app

# Access frontend
minikube service todo-chatbot-frontend -n todo-app

# Upgrade
helm upgrade todo-chatbot ./todo-chatbot -n todo-app --set ...

# Uninstall
helm uninstall todo-chatbot -n todo-app
```

## Quality Checklist

- [ ] `helm lint` passes with no errors
- [ ] `helm template` renders all templates without errors
- [ ] Every container has livenessProbe + readinessProbe
- [ ] Every container has resource requests + limits
- [ ] Zero hardcoded secrets (all via Secret resource + values override)
- [ ] Namespace consistently applied on all resources
- [ ] Labels and selectors match across deployment/service pairs
- [ ] values.yaml has inline comments on every entry
- [ ] Install commands include `--dry-run --debug` examples
- [ ] NOTES.txt provides access and verification instructions

## Output Format

1. **Directory tree** — annotated folder structure
2. **File contents** — full, copy-pasteable YAML for every file
3. **Install commands** — prerequisite, install, verify, access, upgrade, uninstall
4. **Customization notes** — which values to override for common scenarios
