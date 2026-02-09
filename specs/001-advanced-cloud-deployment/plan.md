# Implementation Plan: Phase V — Advanced Cloud Deployment

**Branch**: `main` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-advanced-cloud-deployment/spec.md`
**Owner**: Shumaila

---

## Summary

Transform the Todo AI Chatbot from a local Minikube deployment into a production-grade, event-driven distributed system. The plan covers 6 Alembic migrations (priorities, tags, search, due dates, recurrence, reminders), 3 Kafka topics with 4 consumer microservices wired through Dapr sidecars, cloud deployment to Oracle OKE (always-free), a GitHub Actions CI/CD pipeline, and a Prometheus + Grafana + Loki monitoring stack. Total estimated effort: 8-10 weeks.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Next.js 14 (frontend)
**Primary Dependencies**: FastAPI, SQLModel, Alembic, aiokafka, httpx (Dapr client), Dapr v1.13+, Helm v3
**Storage**: Neon PostgreSQL (free tier) — tasks, conversations, tags, audit logs
**Event Streaming**: Kafka via Redpanda Cloud Serverless (cloud) / Strimzi operator (Minikube)
**Testing**: pytest + pytest-cov (>80%), mocked Kafka for event tests
**Target Platform**: Kubernetes — Minikube (local), Oracle OKE (cloud primary)
**Project Type**: Web application (backend + frontend + consumer microservices)
**Performance Goals**: p95 < 500ms CRUD, < 100ms event publish, < 1s search for 10K tasks
**Constraints**: $0/month cloud spend (always-free tiers), < 8GB RAM on Minikube, < 15min CI/CD pipeline
**Scale/Scope**: Single-tenant per-user isolation, HPA 1-3 replicas, 3 Kafka topics

---

## Constitution Check

*GATE: Passed — all items verified against constitution v4.0.0*

| Gate | Status | Evidence |
| ---- | ------ | -------- |
| 2.1 Dapr Abstraction | PASS | All app code uses `localhost:3500`; `USE_DAPR` toggle for fallback |
| 2.2 Events After Commit | PASS | Event emission explicitly post-`session.commit()` in every feature |
| 2.3 Safety (no lost/dupes/loops) | PASS | `acks=all`, idempotent consumers, `recurrence_depth` cap at 1000 |
| 2.4 Cost Control | PASS | OKE always-free, Redpanda Cloud free, Neon free, GHCR free |
| 2.5 Fallbacks | PASS | Strimzi for Kafka, AKS/GKE for OKE, `USE_DAPR=false` for Dapr |
| 2.6 User Isolation | PASS | All queries filter by `user_id`; tags, events, audit scoped per-user |
| Priority Ladder | PASS | Event safety > Dapr > cost > features > CI/CD > polish |

---

## 1. Phase Overview & Timeline

Phase V transforms the Todo AI Chatbot into its final form — a production-grade, event-driven distributed system running on cloud Kubernetes. Building on Phase III (FastAPI + MCP + Neon) and Phase IV (Minikube + Helm), we add intermediate features (priorities, tags, search/filter/sort), advanced features (due dates, recurring tasks, reminders), wire all state changes through Kafka events via Dapr sidecars, deploy to Oracle OKE (always-free), automate with GitHub Actions, and add monitoring with Prometheus + Grafana + Loki.

**Estimated Duration**: 8-10 weeks
**Start Date**: February 2026

| Week | Milestone | Deliverable |
| ---- | --------- | ----------- |
| 1-2 | V.1 | Intermediate + advanced features with migrations |
| 3 | V.2 | Kafka topics, event schemas, producer/consumer services |
| 4 | V.3 | Full Dapr sidecar adoption + building blocks |
| 5-6 | V.4 | Minikube end-to-end with Dapr + Strimzi Kafka |
| 7 | V.5 | Oracle OKE provisioning + Redpanda Cloud |
| 8 | V.6 | Production cloud deployment + TLS + HPA |
| 9-10 | V.7 | CI/CD pipeline + monitoring + final validation |

---

## 2. Dependencies from Previous Phases

### Phase III (Must Be Stable)
- FastAPI backend with CRUD endpoints for tasks
- MCP server with `add_task`, `update_task`, `list_tasks`, `complete_task`, `delete_task` tools
- Neon PostgreSQL with `user`, `task`, `conversations`, `messages` tables
- Better Auth + JWT authentication working
- OpenAI Agents SDK agent runner functional

### Phase IV (Must Be Stable)
- Docker Desktop + WSL2 Ubuntu environment
- Minikube v1.38.0+ with Docker driver
- Helm chart (`charts/todo-app/`) deploying frontend + backend
- Backend and frontend Dockerfiles building successfully
- `values.yaml` with secrets, probes, and resource limits

---

## 3. High-Level Roadmap

### V.1 — Intermediate & Advanced Feature Implementation (Weeks 1-2)

**Objective**: Add all 8 features with 6 Alembic migrations, extended MCP tools, and >80% test coverage.

**Key Deliverables**:
- Alembic migrations 004-009 (priority enum, tags, search vector, due date type, recurrence, reminders)
- Extended MCP tools: `add_task`/`update_task` with new params, `list_tasks` with search/filter/sort/pagination, `list_tags`, `list_recurring_tasks`
- Updated Pydantic schemas and validation
- Unit tests for each feature (>80% coverage)

**Primary Agent**: Feature Developer
**Effort**: 8-10 days

**Acceptance Criteria**:
- All 6 migrations run forward + backward cleanly
- `list_tasks` supports search, 7 filter params, 5 sort options, pagination
- Recurring task creates next occurrence on completion (unit test with mocked event)
- Reminder query returns correct tasks within time window

---

### V.2 — Event-Driven Backbone & Kafka Integration (Week 3)

**Objective**: Implement domain event emission, Kafka topic schemas, and 4 consumer microservices.

**Key Deliverables**:
- `TaskEvent` dataclass with `event_id`, `event_type`, `user_id`, `task_id`, `data`, `schema_version`, `timestamp`
- Event emitter module (fires after `session.commit()`, fire-and-forget with 3x retry)
- Transport abstraction: `USE_DAPR=true` → Dapr HTTP publish, `false` → direct aiokafka
- 4 consumer services: Recurring Task, Notification, Audit Logger, Real-time Sync
- Dead-letter queue handling for failed messages

**Primary Agent**: Event-Driven Architecture
**Effort**: 5-7 days

**Acceptance Criteria**:
- Creating a task emits `task.created` event with correct schema
- Completing a recurring task triggers next occurrence creation via consumer
- Duplicate events are idempotently processed (same `event_id` → skip)
- Failed events land in dead-letter topic

---

### V.3 — Full Dapr Sidecar Adoption (Week 4)

**Objective**: Configure all 5 Dapr building blocks and ensure zero direct infrastructure calls in app code.

**Key Deliverables**:
- Component YAMLs: `pubsub.kafka`, `state.postgresql`, `bindings.cron`, `secretstores.kubernetes`
- Dapr client module (`httpx` to `localhost:3500`) for publish, state, secrets
- Cron binding for reminder checks (every 1 minute)
- Service invocation config for frontend → backend
- `dapr.enabled` Helm conditional for all component templates

**Primary Agent**: Dapr Integration
**Effort**: 4-5 days

**Acceptance Criteria**:
- `grep -r "from kafka\|from aiokafka" backend/` returns zero results when `USE_DAPR=true`
- Swap `pubsub.kafka` → `pubsub.redis` in YAML → app still works
- Secrets retrieved via Dapr API, with env-var fallback
- All pods show 2/2 containers (app + daprd sidecar)

---

### V.4 — Local Minikube End-to-End (Weeks 5-6)

**Objective**: Deploy the full stack on Minikube with Dapr + Strimzi Kafka, verified with end-to-end tests.

**Key Deliverables**:
- `deploy-local.sh`: staged orchestration (Minikube → Dapr → Strimzi → topics → images → Helm)
- `teardown-local.sh`: reverse cleanup
- Updated Helm chart with Dapr annotations, consumer deployments, Kafka components
- `values-local.yaml` with Minikube-specific overrides
- End-to-end test: create task → event → consumer → audit log

**Primary Agent**: Local Deployment
**Effort**: 8-10 days

**Acceptance Criteria**:
- Cold start → all pods Running in < 10 minutes
- `kubectl top nodes` shows < 80% memory utilization
- All pods 2/2 containers (app + daprd)
- E2E: create recurring task → complete → next occurrence auto-created

---

### V.5 — Cloud Environment Provisioning (Week 7)

**Objective**: Provision Oracle OKE cluster, Redpanda Cloud topics, and cloud infrastructure.

**Key Deliverables**:
- Oracle OKE cluster (always-free: 4 OCPUs, 24GB RAM, 2 worker nodes)
- `dapr init -k` on OKE cluster
- Redpanda Cloud Serverless: 3 topics with SASL credentials
- NGINX Ingress Controller with LoadBalancer
- cert-manager for TLS (Let's Encrypt)
- Cloud secrets in Kubernetes (DB URL, API keys, Kafka credentials)

**Primary Agent**: Cloud Deployment
**Effort**: 3-5 days

**Acceptance Criteria**:
- `kubectl get nodes` shows 2 healthy nodes on OKE
- `dapr status -k` shows all Dapr components healthy
- Redpanda Cloud dashboard shows 3 topics accepting messages
- `curl -I https://<domain>` returns 200 with valid TLS certificate

---

### V.6 — Production Cloud Deployment & Validation (Week 8)

**Objective**: Deploy the full app to OKE with `values-cloud.yaml` and validate all features work in cloud.

**Key Deliverables**:
- `values-cloud.yaml` with GHCR image paths, HPA config, cloud Kafka brokers
- Docker images built and pushed to GHCR with git SHA tags
- `helm upgrade --install -f values-cloud.yaml --atomic --timeout 10m`
- HPA configured: min 1, max 3, target 70% CPU
- Cloud smoke test: full user journey (create, prioritize, tag, search, complete recurring, get reminder)

**Primary Agent**: Cloud Deployment
**Effort**: 3-5 days

**Acceptance Criteria**:
- All pods Running + 2/2 containers on OKE
- Public URL accessible with valid TLS
- Task created via chatbot → event visible in Redpanda Cloud console within 5s
- HPA scales under load test (1 → 2 replicas)

---

### V.7 — CI/CD Pipeline & Observability (Weeks 9-10)

**Objective**: Automate the full pipeline and add production monitoring.

**Key Deliverables**:
- `.github/workflows/deploy.yml`: lint → test → build → push → deploy
- `.github/workflows/rollback.yml`: `workflow_dispatch` manual rollback
- Prometheus + Grafana + Loki Helm deployment
- 4 Grafana dashboards as ConfigMaps (API metrics, Kafka lag, pod resources, alerts)
- 4 PrometheusRule alert CRDs (restarts, errors, latency, Kafka lag)

**Primary Agent**: CI/CD Pipeline + Monitoring & Logging
**Effort**: 6-8 days

**Acceptance Criteria**:
- Push to main → full pipeline < 15 minutes
- Failed test → deploy skipped
- Bad deploy → atomic rollback
- Grafana dashboards load in "Todo Chatbot" folder
- Each alert fires when intentionally triggered
- Total monitoring memory < 1.5GB on Minikube

---

## 4. Agent Assignments & Responsibilities

| Agent | Milestones | Key Responsibilities |
| ----- | ---------- | -------------------- |
| Feature Developer | V.1 | Migrations 004-009, MCP tools, schemas, unit tests |
| Event-Driven Architecture | V.2 | Event schemas, producers, consumers, dead-letter queues |
| Dapr Integration | V.3, V.4 | Component YAMLs, Dapr client, cron binding, `USE_DAPR` toggle |
| Local Deployment | V.4 | `deploy-local.sh`, Strimzi Kafka, Helm updates, E2E tests |
| Cloud Deployment | V.5, V.6 | OKE provisioning, Redpanda Cloud, TLS, HPA, `values-cloud.yaml` |
| CI/CD Pipeline | V.7 | GitHub Actions workflows, Docker caching, rollback |
| Monitoring & Logging | V.7 | Prometheus, Grafana, Loki, alert rules, dashboards |

### Agent Collaboration Points

- V.1 → V.2: Feature Developer hands off event emission hooks to Event-Driven Architecture
- V.2 → V.3: Event-Driven Architecture hands off transport layer to Dapr Integration
- V.3 → V.4: Dapr Integration provides component YAMLs to Local Deployment for Helm
- V.4 → V.5: Local Deployment validates stack; Cloud Deployment mirrors to OKE
- V.6 → V.7: Cloud Deployment provides working cluster; CI/CD Pipeline automates it

---

## 5. Resource & Tooling Requirements

### Cloud Accounts

| Provider | Tier | Required For | Setup Time |
| -------- | ---- | ------------ | ---------- |
| Oracle Cloud | Always-free | OKE cluster (primary) | 1-2 hours |
| Redpanda Cloud | Serverless free | Managed Kafka (cloud) | 30 minutes |
| GitHub | Free (public repo) | GHCR + Actions CI/CD | Already exists |
| Azure (fallback) | $200 / 30 days | AKS if OKE unavailable | 1 hour |
| Google Cloud (fallback) | $300 / 90 days | GKE if both above fail | 1 hour |

### API Keys & Credentials

- `DATABASE_URL` — Neon PostgreSQL (existing from Phase III)
- `BETTER_AUTH_SECRET` — JWT signing (existing)
- `OPENAI_API_KEY` — Agent runner (existing)
- `KAFKA_BROKERS` — Redpanda Cloud bootstrap URL (new)
- `KAFKA_USERNAME` / `KAFKA_PASSWORD` — Redpanda SASL credentials (new)
- `KUBECONFIG` — OKE cluster access (new)

### Local Tooling

- Dapr CLI v1.13+ (`dapr init -k`)
- Strimzi Kafka operator (Minikube fallback)
- Helm v3.x (existing from Phase IV)
- Minikube v1.38.0+ (existing from Phase IV)
- Docker Desktop with WSL2 (existing)

### Budget

**Target: $0/month** using always-free tiers for all primary services. AKS/GKE credits used only as documented fallback.

---

## 6. Risk Register & Mitigation Plan

| # | Risk | Likelihood | Impact | Mitigation | Owner |
| - | ---- | ---------- | ------ | ---------- | ----- |
| 1 | OKE free tier unavailable or insufficient | Low | High | Fallback: AKS ($200) → GKE ($300) | Cloud Deployment |
| 2 | Redpanda Cloud blocked/rate-limited | Medium | Medium | Fallback: Strimzi self-hosted on K8s | Event-Driven Arch |
| 3 | Dapr sidecar crashes Minikube (memory) | Medium | High | Tune sidecar limits to 64Mi; total stack < 8GB | Local Deployment |
| 4 | Events emitted before DB commit | Low | Critical | Code review gate: emit only post-`session.commit()` | Feature Developer |
| 5 | Recurring task infinite loop | Very Low | Critical | `recurrence_depth` CHECK constraint; max 1000 | Feature Developer |
| 6 | Duplicate reminders sent | Medium | High | `reminder_sent` flag + `event_id` idempotency | Event-Driven Arch |
| 7 | Kafka consumer lag delays reminders | Medium | Medium | Grafana alert at lag > 1000; scale consumers via HPA | Monitoring |
| 8 | Secrets leaked in git or CI logs | Low | Critical | Dapr secrets API; `${{ secrets.* }}`; pre-commit hook | CI/CD Pipeline |
| 9 | Alembic migration breaks existing data | Medium | High | All new columns nullable; test upgrade + downgrade | Feature Developer |
| 10 | Full-text search slow on large datasets | Low | Medium | GIN index + pagination; max 100 results per page | Feature Developer |

---

## 7. Prioritization & Decision Gates

### Must-Have vs Nice-to-Have

| Priority | Feature | Rationale |
| -------- | ------- | --------- |
| Must-have | Priorities (P1-P4), Tags, Search/Filter/Sort | Core usability — foundational for chatbot |
| Must-have | Due dates, Recurring tasks, Reminders | Drive the event-driven architecture |
| Must-have | Kafka topics + Dapr Pub/Sub | Core architecture — events-first design |
| Must-have | Minikube full deployment | Local validation before cloud |
| Must-have | OKE cloud deployment | Primary deliverable of Phase V |
| Nice-to-have | Real-time sync consumer | Enhances UX but not critical for demo |
| Nice-to-have | Audit logger consumer | Useful for debugging, not user-facing |
| Nice-to-have | Full CI/CD pipeline | Can deploy manually if pipeline not ready |
| Nice-to-have | Loki log aggregation | Prometheus + Grafana sufficient for demo |

### Decision Gates

| Gate | Condition | Decision |
| ---- | --------- | -------- |
| G1 | V.1 features pass all unit tests | Proceed to V.2 event wiring |
| G2 | V.2 events emit correctly with mocked Kafka | Proceed to V.3 Dapr adoption |
| G3 | V.4 Minikube E2E passes (create → event → consumer) | Proceed to V.5 cloud provisioning |
| G4 | V.5 OKE cluster healthy + Redpanda topics created | Proceed to V.6 cloud deployment |
| G5 | OKE free tier exhausted | KILL: Switch to AKS with $200 credits |

---

## 8. Weekly Rhythm & Checkpoints

### Cadence

1. **Monday**: Review spec, assign agent tasks for the week
2. **Daily**: Agent progress check via Claude Code (status of current milestone)
3. **Friday**: Demo checkpoint — show working feature from current milestone
4. **End of Milestone**: Full demo + documentation handoff before next milestone starts

### Demo Checkpoints

| Milestone | Demo |
| --------- | ---- |
| V.1 | Create task with priority P1, tags "work,urgent", search by "work" |
| V.2 | Complete recurring task → see next occurrence auto-created in logs |
| V.3 | Show 2/2 pods, swap pubsub.kafka → pubsub.redis → app works |
| V.4 | Full Minikube E2E: create → event → consumer → audit |
| V.5 | `kubectl get nodes` on OKE, Redpanda Cloud dashboard with topics |
| V.6 | Public URL with TLS, create task via chatbot, event in Redpanda |
| V.7 | Push to main → pipeline runs → deploy to OKE → verify via curl |

### Documentation Handoffs

- After V.1: Updated API contracts in `contracts/`
- After V.4: `deploy-local.sh` + `teardown-local.sh` scripts committed
- After V.6: `values-cloud.yaml` + OKE setup guide
- After V.7: Full deployment runbook + monitoring dashboard screenshots

---

## 9. Success Definition for Phase Completion

Phase V is **complete** when all of the following are true:

1. All 8 features working (priorities, tags, search, filter, sort, due dates, recurring tasks, reminders) with >80% test coverage
2. All CRUD operations emit domain events after DB commit — zero events lost under normal operation
3. Recurring tasks auto-create next occurrence within 10 seconds of completion
4. Reminders fire within 1 minute of scheduled time, never duplicated
5. Full stack deploys to Oracle OKE via `helm upgrade --install -f values-cloud.yaml`
6. Public URL accessible with valid TLS certificate
7. CI/CD pipeline completes in under 15 minutes (push → production)
8. Monitoring dashboards show API metrics, Kafka lag, pod resources, and alerts fire correctly
9. Monthly cloud cost = $0 using always-free tiers
10. Entire stack deployable locally on Minikube in under 10 minutes via `deploy-local.sh`

### Final Demo Flow

```
User opens chatbot → creates task "Weekly standup" with priority P1,
  tags ["work","meetings"], recurrence_rule="weekly",
  due_date="2026-02-10T09:00:00Z", reminder_minutes=30
→ Task created in Neon PostgreSQL
→ task.created event published via Dapr Pub/Sub to Kafka
→ Audit Logger writes log entry
→ 30 min before due date: cron binding fires → Notification Service sends reminder
→ User completes task via chatbot
→ task.completed event triggers Recurring Task Service
→ New task auto-created with due_date="2026-02-17T09:00:00Z"
→ All visible in Grafana dashboard: event count, consumer lag = 0, API p95 < 500ms
```

---

## Project Structure

### Documentation (this feature)

```text
specs/001-advanced-cloud-deployment/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart guide
├── contracts/           # Phase 1 API contracts
│   ├── mcp-tools.md     # Extended MCP tool schemas
│   ├── events.md        # Kafka event schemas
│   └── dapr-components.md # Dapr component specs
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── models/              # SQLModel entities (Task extended, Tag new)
├── schemas/             # Pydantic request/response schemas
├── alembic/versions/    # Migrations 004-009
├── mcp/
│   ├── tools/           # Extended MCP tools
│   ├── schemas/         # Extended param schemas
│   └── crud/            # CRUD with search/filter/sort
├── agent/               # OpenAI agent runner
├── events/              # NEW: Event emitter + transport abstraction
│   ├── emitter.py       # Post-commit event publisher
│   ├── schemas.py       # TaskEvent, ReminderEvent dataclasses
│   └── transport.py     # Dapr HTTP vs direct aiokafka toggle
├── consumers/           # NEW: Kafka consumer microservices
│   ├── recurring.py     # Recurring Task Service
│   ├── notification.py  # Notification Service
│   ├── audit.py         # Audit Logger
│   └── sync.py          # Real-time Sync
├── api/                 # FastAPI endpoints
├── tests/               # >80% coverage per feature
└── Dockerfile

frontend/
├── app/                 # Next.js App Router
├── components/          # UI components (tags, priority badges, filters)
└── Dockerfile

charts/todo-app/
├── templates/
│   ├── dapr/            # NEW: Dapr component YAMLs (conditional)
│   ├── consumers/       # NEW: Consumer deployment templates
│   └── monitoring/      # NEW: Prometheus rules, Grafana ConfigMaps
├── values.yaml          # Base values
├── values-local.yaml    # NEW: Minikube overrides
└── values-cloud.yaml    # NEW: OKE/cloud overrides

scripts/
├── deploy-local.sh      # NEW: Minikube staged startup
└── teardown-local.sh    # NEW: Minikube cleanup

.github/workflows/
├── deploy.yml           # NEW: CI/CD pipeline
└── rollback.yml         # NEW: Manual rollback
```

**Structure Decision**: Web application pattern (existing from Phase III/IV) with new `events/`, `consumers/`, and extended `charts/` directories.

---

## Complexity Tracking

No constitution violations detected. All design decisions align with the 6 non-negotiables.
