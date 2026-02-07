# Todo AI Chatbot — Phase V: Advanced Cloud Deployment

A production-grade Todo AI Chatbot with priority levels, tags, due dates, recurring tasks, and reminders. All wired through Kafka events via Dapr sidecars, deployed on Minikube with CI/CD and cloud-ready Helm charts.

Cloud-Native Todo AI Chatbot with Event-Driven Architecture
Phase V Thumbnail
https://youtu.be/-Z04jG9uzEg
Project Overview
Phase V completes the evolution of the Todo AI Chatbot into a production-grade, event-driven, cloud-native application.
It builds on Phase III (AI chatbot with MCP tools) and Phase IV (local Minikube + Helm) by adding:

Intermediate features: priorities, tags, search, filter, sort
Advanced features: recurring tasks, due dates, reminders/notifications
Full event-driven architecture with Kafka (Redpanda) topics: task-events, reminders, task-updates
Dapr sidecar runtime for decoupling (Pub/Sub, State, Bindings/cron, Secrets, Service Invocation)
Local deployment on Minikube with Dapr + Redpanda
Production deployment on Oracle Cloud Always Free OKE (4 OCPUs, 24 GB RAM)
Basic CI/CD via GitHub Actions
Monitoring & logging basics (Prometheus/Grafana or cloud-native)

This phase demonstrates modern microservices, loose coupling, and scalability — turning a simple CRUD app into a resilient, real-time system.
Technology Stack – Phase V
LayerTechnologyPurposeFrontendNext.js 14+ (App Router) + ChatKitResponsive UI with natural language chatBackendFastAPI + SQLModel + UvicornCore API + MCP toolsAI FrameworkOpenAI Agents SDKChatbot reasoning & tool callingDatabaseNeon PostgreSQL (serverless)Persistent tasks & conversationsMessagingRedpanda Cloud Serverless (Kafka-comp.)Event-driven topics (task-events, reminders)Runtime AbstractionDapr sidecarPub/Sub, State, Cron bindings, SecretsLocal K8sMinikube + Docker driverTesting & development clusterCloud K8sOracle Cloud Always Free OKEProduction-grade deploymentPackagingHelm v3/v4Application deployment manifestsCI/CDGitHub ActionsBuild → test → deploy pipelineMonitoringPrometheus + Grafana (basic)Cluster & app metrics
## Features

| Feature | Description |
|---------|-------------|
| **Priorities (P1-P4)** | 4-level priority system: P1 (Critical), P2 (High), P3 (Medium), P4 (Low) |
| **Tags** | Free-form tags, many-to-many with tasks, per-user isolation, max 10 per task |
| **Full-Text Search** | PostgreSQL TSVECTOR + GIN index for fast natural language search |
| **Due Dates** | TIMESTAMPTZ with range filtering (due_before, due_after) |
| **Recurring Tasks** | Daily, weekly, monthly recurrence with auto-creation on completion |
| **Reminders** | Configurable minutes-before-due reminder with cron-triggered checks |
| **Search/Filter/Sort** | Combined search + priority/tag/completion/date filters + sort + pagination |
| **Event-Driven** | All CRUD operations emit domain events to Kafka via Dapr Pub/Sub |
| **Dapr Sidecars** | App talks to localhost:3500 — infrastructure swappable via YAML |
| **Dual Transport** | USE_DAPR toggle switches between Dapr HTTP and direct aiokafka |

## Architecture

```
User -> NGINX Ingress -> Frontend (Next.js) -> Backend (FastAPI)
                                                    |
                                              Dapr Sidecar (localhost:3500)
                                                    |
                                        +-----------+-----------+
                                        |           |           |
                                    Pub/Sub     State Store   Secrets
                                   (Kafka)    (PostgreSQL)   (K8s)
                                        |
                              +---------+---------+
                              |                   |
                        Recurring Task      Notification     Audit
                          Consumer            Consumer       Logger
```

See [spec.md](specs/001-advanced-cloud-deployment/spec.md) for the full mermaid architecture diagram.

## Quick Start

### Local Development (No K8s)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
USE_DAPR=false python -m uvicorn main:app --reload
```

### Minikube with Dapr + Kafka

```bash
# One command deploys everything
bash scripts/deploy-local.sh

# Access the app
minikube service todo-frontend -n todo-app

# Clean up
bash scripts/teardown-local.sh
```

### Cloud (Oracle OKE)

```bash
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-cloud.yaml \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  --set backend.secrets.openaiApiKey="$OPENAI_API_KEY" \
  --namespace todo-app --create-namespace --atomic
```

## Demo Flow (for judges)

1. **Create a task with priority + tags + recurrence**:
   > "Add a P1 task called 'Weekly team standup' tagged 'work' and 'meetings' that recurs weekly with a 30-minute reminder"

2. **Search and filter**:
   > "Show me all P1 tasks tagged 'work' sorted by due date"

3. **Complete the recurring task**:
   > "Mark 'Weekly team standup' as complete"

4. **See the magic** — the recurring task consumer auto-creates the next occurrence with the due date advanced by 1 week

5. **Verify events**: Check Kafka topic `task-events` for the `task.completed` and `task.created` events

## Project Structure

```
backend/
  alembic/versions/     004-009 migrations (priority, tags, search, dates, recurrence, reminders)
  events/               Event emitter + transport abstraction (Dapr/Kafka)
  consumers/            Recurring, Notification, Audit consumers (Dapr subscriptions)
  models/               SQLModel Task + Tag + TaskTag
  mcp/                  MCP tools with search/filter/sort/pagination
charts/todo-app/
  templates/dapr/       Dapr component YAMLs (pubsub, statestore, cron, secrets)
  templates/monitoring/ Prometheus alerts + Grafana dashboard ConfigMap
  templates/            Deployments, services, 3 consumers, ingress
  values.yaml           Base values
  values-local.yaml     Minikube + Dapr + Strimzi Kafka
  values-cloud.yaml     OKE + Redpanda + TLS
  values-aks.yaml       Azure AKS fallback
  values-gke.yaml       Google GKE fallback
scripts/
  deploy-local.sh       Minikube full-stack deployment
  teardown-local.sh     Clean teardown
.github/workflows/
  deploy.yml            CI/CD: lint -> test -> build -> push -> deploy
  rollback.yml          Manual rollback via Helm revision
specs/
  001-advanced-cloud-deployment/
    spec.md             Full specification (14 sections)
    plan.md             Implementation plan (7 milestones)
    tasks.md            16-task fast-track plan
    data-model.md       ER diagram + entity specs
    contracts/          MCP tools, events, Dapr components
```

## Key Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | Yes | JWT signing secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `USE_DAPR` | No | Toggle Dapr (true) vs direct Kafka (false) |
| `KAFKA_BROKERS` | If USE_DAPR=false | Kafka bootstrap servers |

## Phases

- **Phase III**: Backend + MCP tools + AI chatbot + conversation persistence
- **Phase IV**: Docker + Minikube + Helm charts + kubectl-ai + kagent
- **Phase V**: Priorities, tags, search, recurrence, reminders, Kafka events, Dapr sidecars, CI/CD, cloud deployment

## Consumer Microservices

| Consumer | Topic | Purpose | Port |
|----------|-------|---------|------|
| **Recurring** | `task-events` | Auto-creates next task occurrence on completion | 8001 |
| **Notification** | `reminders` | Processes reminder.due events, marks reminder_sent | 8002 |
| **Audit Logger** | `task-events` | Structured JSON logging of all events (Loki-compatible) | 8003 |

## Real-time Sync

WebSocket endpoint at `/ws/{user_id}` broadcasts task events to connected clients for live dashboard updates.

## Monitoring

- **Prometheus**: 4 alert rules (API error rate, latency, Kafka lag, pod restarts)
- **Grafana**: Pre-configured dashboard with API metrics, consumer lag, pod health panels

## Cloud Fallbacks

| Provider | Values File | Notes |
|----------|-------------|-------|
| Oracle OKE (primary) | `values-cloud.yaml` | Always-free, 4 OCPUs, 24GB RAM |
| Azure AKS | `values-aks.yaml` | Application Gateway ingress, ACR registry |
| Google GKE | `values-gke.yaml` | GCE ingress, Workload Identity |

## Tests

- **Phase V Unit Tests**: 25 tests covering priorities, tags, search, recurrence, reminders, event schemas
- Run: `cd backend && pytest tests/test_phase_v.py -v`

## Documentation

- [Cloud Deployment Guide](docs/cloud-deployment-guide.md) — OKE/AKS/GKE deployment instructions
- [CI/CD Pipeline](docs/cicd-pipeline.md) — GitHub Actions workflow details
- [Demo Assets](demo/README.md) — Screenshots and demo walkthrough
- [Full Spec](specs/001-advanced-cloud-deployment/spec.md) — Complete Phase V specification

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Next Steps / Future Ideas

- Email/SMS notifications via Twilio or SendGrid Dapr binding
- Advanced monitoring with SLOs and error budgets
- Load testing with Locust
- Multi-user task sharing

---

Made with love in Karachi, Pakistan
Shumaila - February 2026
Hackathon II - Evolution of Todo - Phase V Submission

