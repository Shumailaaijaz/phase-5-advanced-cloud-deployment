# Dapr Component Contracts: Phase V

**Date**: 2026-02-07 | **Spec**: [../spec.md](../spec.md)

---

## Component Summary

| Component | Type | Name | Location |
| --------- | ---- | ---- | -------- |
| Pub/Sub | `pubsub.kafka` | `task-pubsub` | `charts/todo-app/templates/dapr/pubsub.yaml` |
| State Store | `state.postgresql` | `task-statestore` | `charts/todo-app/templates/dapr/statestore.yaml` |
| Cron Binding | `bindings.cron` | `reminder-cron` | `charts/todo-app/templates/dapr/cron-binding.yaml` |
| Secret Store | `secretstores.kubernetes` | `k8s-secrets` | `charts/todo-app/templates/dapr/secretstore.yaml` |

All templates are conditional on `{{ if .Values.dapr.enabled }}`.

---

## Pub/Sub Component (pubsub.kafka)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: task-pubsub
  namespace: {{ .Values.global.namespace }}
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      secretKeyRef:
        name: kafka-secrets
        key: brokers
    - name: authType
      value: "{{ .Values.kafka.authType }}"
    - name: saslUsername
      secretKeyRef:
        name: kafka-secrets
        key: username
    - name: saslPassword
      secretKeyRef:
        name: kafka-secrets
        key: password
    - name: consumerGroup
      value: "todo-app"
    - name: maxMessageBytes
      value: "1048576"
```

**App Usage**: `POST http://localhost:3500/v1.0/publish/task-pubsub/{topic}`

---

## State Store Component (state.postgresql)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: task-statestore
  namespace: {{ .Values.global.namespace }}
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: backend-secrets
        key: database-url
```

**App Usage**: `GET/POST http://localhost:3500/v1.0/state/task-statestore/{key}`

---

## Cron Binding (bindings.cron)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-cron
  namespace: {{ .Values.global.namespace }}
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 1m"
    - name: direction
      value: "input"
```

**App Usage**: Dapr invokes `POST /reminder-cron` on the backend every 1 minute. Backend queries for due reminders and publishes to `reminders` topic.

---

## Secret Store Component (secretstores.kubernetes)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: k8s-secrets
  namespace: {{ .Values.global.namespace }}
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

**App Usage**: `GET http://localhost:3500/v1.0/secrets/k8s-secrets/{secret-name}`

---

## Dapr Sidecar Annotations (Pod Template)

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "{{ .Values.dapr.appId }}"
  dapr.io/app-port: "{{ .Values.dapr.appPort }}"
  dapr.io/enable-api-logging: "true"
  dapr.io/log-level: "info"
  dapr.io/sidecar-cpu-request: "50m"
  dapr.io/sidecar-memory-request: "64Mi"
  dapr.io/sidecar-cpu-limit: "200m"
  dapr.io/sidecar-memory-limit: "128Mi"
```
