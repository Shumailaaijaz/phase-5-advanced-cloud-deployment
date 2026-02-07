---
name: event-driven-service-creation
description: Create standalone FastAPI microservices that consume Kafka events via Dapr Pub/Sub. Covers Notification Service, Recurring Task Service, Audit Service, and WebSocket Service, each with its own Dockerfile and Helm deployment. Use when building event consumer services for the Phase V architecture.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Event-Driven Service Creation

## Purpose

Create standalone microservices that consume Kafka events via Dapr Pub/Sub: Notification Service (sends reminders), Recurring Task Service (creates next occurrences), Audit Service (stores activity log), and WebSocket Service (broadcasts real-time updates). Each service runs as a separate Kubernetes deployment with its own Dapr sidecar.

## Used by

- Event-Driven Architecture Agent (Agent 2)
- Dapr Integration Agent (Agent 3)
- Local Deployment Agent (Agent 4)

## When to Use

- Creating the Notification Service that processes reminder events
- Building the Recurring Task Service that auto-creates next task occurrences
- Implementing the Audit Service that logs all task operations
- Setting up the WebSocket Service for real-time client sync
- Any new consumer service that subscribes to Kafka topics via Dapr

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_name` | string | Yes | Name of the service |
| `consumed_topics` | list | Yes | Topics this service subscribes to |
| `event_handler` | string | Yes | Business logic description |
| `dapr_app_id` | string | Yes | Dapr application ID |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| FastAPI service | Python | Service with Dapr subscription endpoint |
| Dockerfile | Dockerfile | Container build definition |
| Helm template | YAML | Deployment with Dapr sidecar annotations |
| Health endpoint | Python | Readiness and liveness probes |

## Procedure

### Step 1: Service Structure

```
services/{service_name}/
├── main.py          # FastAPI app with Dapr subscriptions
├── Dockerfile
├── requirements.txt
└── tests/
    └── test_handler.py
```

### Step 2: Dapr Subscription Endpoint

```python
@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "reminders",
            "route": "/events/reminders",
        },
    ]

@app.post("/events/reminders")
async def handle_reminder(request: Request):
    event = await request.json()
    data = event.get("data", {})
    # Process event...
    return {"status": "SUCCESS"}  # Dapr ack
```

### Step 3: Helm Deployment with Dapr Annotations

```yaml
metadata:
  annotations:
    dapr.io/enabled: "true"
    dapr.io/app-id: "notification-service"
    dapr.io/app-port: "8002"
```

### Step 4: Health Endpoint

```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}
```

## Quality Standards

- [ ] Every service exposes `GET /dapr/subscribe` for topic discovery
- [ ] Handlers return `{"status": "SUCCESS"}` for ack, `{"status": "RETRY"}` for retry
- [ ] Each service has own Dockerfile, requirements.txt, Helm template
- [ ] Health endpoints at `GET /health` for K8s probes
- [ ] Services are stateless — persistent state via Dapr or database
- [ ] Dapr app-id annotations match subscription configuration
- [ ] Logging includes event_id for distributed tracing
