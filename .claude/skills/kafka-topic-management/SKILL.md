---
name: kafka-topic-management
description: Create, configure, and validate Kafka topics (task-events, reminders, task-updates) for both self-hosted Strimzi and managed Redpanda Cloud. Define versioned event schemas and partition strategies. Use when setting up the Kafka infrastructure for the event-driven architecture.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Kafka Topic Management

## Purpose

Create, configure, and validate Kafka topics for the event-driven architecture. Covers both self-hosted (Strimzi on Kubernetes) and managed (Redpanda Cloud) deployments. Defines topic schemas, partition strategies, and retention policies.

## Used by

- Event-Driven Architecture Agent (Agent 2)
- Local Deployment Agent (Agent 4) — Strimzi on Minikube
- Cloud Deployment Agent (Agent 5) — Redpanda Cloud

## When to Use

- Creating the three core topics: task-events, reminders, task-updates
- Defining versioned event schemas (TaskEvent, ReminderEvent, TaskUpdateEvent)
- Configuring topic partitions and retention policies
- Setting up Strimzi KafkaTopic CRDs for Kubernetes
- Creating topics on Redpanda Cloud via CLI

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_target` | string | Yes | "minikube" or "cloud" |
| `topics` | list | Yes | Topic definitions (name, partitions, retention) |
| `kafka_namespace` | string | No | Kubernetes namespace (default: "kafka") |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Strimzi CRD YAML | YAML | KafkaTopic resources for K8s |
| Event schemas | Python | Dataclass definitions with JSON serialization |
| Topic commands | bash | Creation and verification commands |

## Procedure

### Step 1: Define Topics

| Topic | Partitions (local) | Partitions (cloud) | Retention | Purpose |
|-------|-------|--------|-----------|---------|
| task-events | 1 | 3 | 7 days | All CRUD operations |
| reminders | 1 | 1 | 1 day | Scheduled reminders |
| task-updates | 1 | 3 | 1 hour | Real-time sync |

### Step 2: Create Strimzi CRDs (Minikube)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  namespace: kafka
  labels:
    strimzi.io/cluster: taskflow-kafka
spec:
  partitions: 1
  replicas: 1
  config:
    retention.ms: "604800000"
```

### Step 3: Define Event Schemas

```python
@dataclass
class TaskEvent:
    event_id: str          # UUID4
    event_type: str        # created|updated|completed|deleted
    task_id: str
    user_id: str
    task_data: Dict[str, Any]
    timestamp: str         # ISO 8601 UTC
    schema_version: int = 1
```

### Step 4: Verify

```bash
# Strimzi
kubectl get kafkatopics -n kafka

# Redpanda Cloud
rpk topic list --brokers $BROKER_URL
rpk topic describe task-events
```

## Quality Standards

- [ ] All schemas include `schema_version` for evolution
- [ ] Every event has unique `event_id` (UUID4) for idempotency
- [ ] Timestamps in ISO 8601 UTC
- [ ] Partition key is `user_id` for per-user ordering
- [ ] Strimzi CRD validates with `kubectl apply --dry-run=client`
- [ ] Minikube: 1 replica; cloud: 3 replicas for fault tolerance
