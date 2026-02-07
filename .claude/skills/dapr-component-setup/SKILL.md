---
name: dapr-component-setup
description: Define and configure Dapr component YAMLs for Pub/Sub (Kafka), State Management, Service Invocation, Bindings (cron), and Secrets Management. Create swappable components and Python HTTP client for Dapr APIs. Use when integrating Dapr building blocks into the Todo Chatbot.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Dapr Component Setup

## Purpose

Define and configure Dapr component YAML files for all five building blocks: Pub/Sub (Kafka), State Management (Redis/PostgreSQL), Service Invocation, Bindings (cron for reminders), and Secrets Management. Components are swappable without code changes.

## Used by

- Dapr Integration Agent (Agent 3)
- Local Deployment Agent (Agent 4)
- Cloud Deployment Agent (Agent 5)

## When to Use

- Configuring Dapr Pub/Sub backed by Kafka/Redpanda
- Setting up Dapr State Store for conversation state
- Enabling Dapr Service Invocation between frontend and backend
- Creating cron bindings for scheduled reminders
- Configuring Dapr Secrets store (Kubernetes or cloud vault)
- Switching component backends between environments

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_block` | string | Yes | pubsub, state, bindings, secrets, or service-invocation |
| `backend_type` | string | Yes | Implementation (kafka, redis, postgres, kubernetes) |
| `deployment_target` | string | Yes | "minikube" or "cloud" |
| `component_name` | string | Yes | Dapr component name |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Component YAML | YAML | Dapr component definition |
| Helm values | YAML | Configuration entries in values.yaml |
| Python client | Python | HTTP client for Dapr APIs |
| Verification | bash | Component health commands |

## Procedure

### Step 1: Pub/Sub Component (Kafka)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "taskflow-kafka-kafka-bootstrap.kafka.svc:9092"
    - name: authType
      value: "none"
```

### Step 2: State Store Component

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: todo-app-secrets
        key: database-url
```

### Step 3: Cron Binding (Reminders)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-cron
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 1m"
    - name: direction
      value: "input"
```

### Step 4: Python Dapr Client

```python
DAPR_BASE_URL = "http://localhost:3500/v1.0"

async def dapr_publish(pubsub_name, topic, data):
    url = f"{DAPR_BASE_URL}/publish/{pubsub_name}/{topic}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data)
        resp.raise_for_status()
```

### Step 5: Verify

```bash
dapr components -k -n todo-app
kubectl get components.dapr.io -n todo-app
```

## Quality Standards

- [ ] App code ONLY talks to Dapr HTTP APIs (localhost:3500) — never directly to Kafka
- [ ] All component YAMLs pass `kubectl apply --dry-run=client`
- [ ] Secrets referenced via secretKeyRef — never inline
- [ ] Components swappable: changing pubsub.kafka to pubsub.redis needs zero code changes
- [ ] Sidecar health checked via `GET /v1.0/healthz`
- [ ] Per-environment overrides in Helm values (minikube vs cloud)
- [ ] Error handling on all Dapr HTTP client calls
