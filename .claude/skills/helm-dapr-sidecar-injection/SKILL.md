---
name: helm-dapr-sidecar-injection
description: Update Phase IV Helm chart templates to enable Dapr sidecar injection via pod annotations. Add conditional Dapr configuration, sidecar resource limits, and include Dapr component YAMLs in the chart. Use when preparing Helm charts for Dapr-enabled deployment.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Helm Dapr Sidecar Injection

## Purpose

Update Phase IV Helm chart templates to enable Dapr sidecar injection on all application deployments. Add Dapr annotations, configure sidecar ports, and include Dapr component definitions in the chart. Supports toggling Dapr on/off via Helm values.

## Used by

- Local Deployment Agent (Agent 4)
- Cloud Deployment Agent (Agent 5)
- helm-chart-creator agent

## When to Use

- Adding Dapr sidecar annotations to existing deployment templates
- Configuring Dapr app-id, app-port, and protocol per service
- Setting sidecar resource limits for Minikube compatibility
- Including Dapr component YAMLs in the Helm chart templates directory
- Toggling Dapr globally via `dapr.enabled` in values.yaml

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_template_path` | string | Yes | Path to existing Helm deployment template |
| `dapr_app_id` | string | Yes | Dapr application ID for the service |
| `dapr_app_port` | int | Yes | Port the application listens on |
| `dapr_enabled` | bool | Yes | Whether Dapr is toggled on |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Modified deployment | YAML | Template with Dapr annotations |
| Updated values.yaml | YAML | Dapr configuration section |
| Component templates | YAML | Dapr component files in templates/dapr/ |
| Verification | bash | Sidecar injection check commands |

## Procedure

### Step 1: Add Conditional Annotations

```yaml
annotations:
  {{- if .Values.dapr.enabled }}
  dapr.io/enabled: "true"
  dapr.io/app-id: "{{ .Values.backend.dapr.appId }}"
  dapr.io/app-port: "{{ .Values.backend.service.port }}"
  dapr.io/app-protocol: "http"
  dapr.io/sidecar-cpu-request: "100m"
  dapr.io/sidecar-memory-request: "64Mi"
  dapr.io/sidecar-cpu-limit: "300m"
  dapr.io/sidecar-memory-limit: "128Mi"
  {{- end }}
```

### Step 2: Add Environment Variables

```yaml
env:
  - name: DAPR_HTTP_PORT
    value: "3500"
  - name: USE_DAPR
    value: "{{ .Values.dapr.enabled }}"
```

### Step 3: Create Component Directory

Place Dapr component YAMLs in `charts/todo-app/templates/dapr/`:
- `pubsub-kafka.yaml`
- `statestore.yaml`
- `binding-cron.yaml`
- `secretstore.yaml`

### Step 4: Verify

```bash
helm template todo-chatbot ./charts/todo-app --set dapr.enabled=true | grep dapr
kubectl get pods -n todo-app -o jsonpath='{.items[*].spec.containers[*].name}'
```

## Quality Standards

- [ ] Dapr annotations are conditional: `{{- if .Values.dapr.enabled }}`
- [ ] Chart works without Dapr (backward compatible)
- [ ] Sidecar resource limits set (100m/64Mi request, 300m/128Mi limit)
- [ ] `dapr.io/app-port` matches container's actual listening port
- [ ] `dapr.io/app-id` unique per deployment
- [ ] `helm lint` passes with and without `dapr.enabled=true`
- [ ] Component YAMLs in `templates/dapr/` subdirectory
