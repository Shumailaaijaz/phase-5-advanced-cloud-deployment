# Phase V Tasks — Advanced Cloud Deployment (Hackathon Fast-Track)

**Date**: 2026-02-07 | **Deadline**: 2 AM tonight | **Owner**: Shumaila
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Total Tasks**: 16 | **Estimated Time**: ~5 hours | **MUST tasks**: 7

---

## Phase V Quick Goal (for judges)

A production-grade Todo AI Chatbot with priority levels (P1-P4), tags, due dates, recurring tasks, and reminders — all wired through Kafka events via Dapr sidecars, deployed on Minikube with a working CI/CD pipeline and cloud-ready Helm charts for Oracle OKE.

---

## Must-Have Deliverables (in repo before 2 AM)

1. `backend/alembic/versions/004_*` through `009_*` — 6 Alembic migrations
2. `backend/events/` — Event emitter + transport abstraction module
3. `backend/consumers/` — At least recurring task consumer
4. `charts/todo-app/templates/dapr/` — Dapr component YAMLs
5. `charts/todo-app/values-local.yaml` — Minikube overrides with Dapr enabled
6. `scripts/deploy-local.sh` — Minikube startup script
7. `.github/workflows/deploy.yml` — CI/CD pipeline (even if basic)
8. `specs/001-advanced-cloud-deployment/` — Spec + plan + tasks (already done)

---

## Fast-Track Task List

### Phase 1: DB Features (get the data layer working first)

- [ ] V5-01 🚨 MUST — Alembic migration: upgrade priority enum P1-P4 `backend/alembic/versions/004_priority_enum.py`
  - **Agent**: Feature Developer | **Time**: ⏰ 15 min
  - **What**: Create migration that converts existing "Low"→P4, "Medium"→P3, "High"→P2 via CASE, adds CHECK constraint. Update `models/user.py` Task class: `priority: str = Field(default="P3")`. Update `mcp/schemas/params.py` VALID_PRIORITIES to `["P1","P2","P3","P4"]`.
  - **Done when**: `alembic upgrade 004` runs clean; `alembic downgrade -1` reverses it; existing tasks keep correct priority.

---

- [ ] V5-02 🚨 MUST — Alembic migration: tags table + task_tag junction `backend/alembic/versions/005_tags.py`
  - **Agent**: Feature Developer | **Time**: ⏰ 20 min
  - **What**: Create `tag` table (id SERIAL PK, name VARCHAR(50) NOT NULL, user_id INT FK→user.id CASCADE, created_at TIMESTAMPTZ DEFAULT now()) with UNIQUE(user_id, name). Create `task_tag` junction (task_id INT FK CASCADE, tag_id INT FK CASCADE, PK(task_id, tag_id)). Create SQLModel classes `Tag` and `TaskTag` in `backend/models/tag.py`.
  - **Done when**: `alembic upgrade 005` creates both tables; foreign keys and unique constraint work.

---

- [ ] V5-03 🚨 MUST — Alembic migrations: search, due_date type, recurrence, reminders `backend/alembic/versions/006_*` through `009_*`
  - **Agent**: Feature Developer | **Time**: ⏰ 30 min
  - **What**: Migration 006: add `search_vector TSVECTOR` + GIN index + trigger on task. Migration 007: ALTER `due_date` VARCHAR→TIMESTAMPTZ with data conversion. Migration 008: add `recurrence_rule VARCHAR(100)`, `recurrence_parent_id INT FK→task.id SET NULL`, `recurrence_depth INT DEFAULT 0 CHECK 0-1000`. Migration 009: add `reminder_minutes INT CHECK>=0`, `reminder_sent BOOLEAN DEFAULT false` + partial index. Update Task model in `models/user.py` with all new fields.
  - **Done when**: `alembic upgrade head` runs all 6 migrations clean; `alembic downgrade base` reverses them.

---

- [ ] V5-04 🚨 MUST — Extend MCP tools with new parameters `backend/mcp/schemas/params.py` + `backend/mcp/crud/task.py` + `backend/mcp/tools/*.py`
  - **Agent**: Feature Developer | **Time**: ⏰ 45 min
  - **What**: Update `AddTaskParams` to accept `tags: Optional[List[str]]`, `recurrence_rule: Optional[str]`, `reminder_minutes: Optional[int]`. Update `UpdateTaskParams` same. Update `ListTasksParams` to accept `search`, `priority`, `tag`, `completed`, `due_before`, `due_after`, `sort_by`, `sort_order`, `page`, `page_size`. Update `create_task()` in crud to handle tags (auto-create if not exist), recurrence fields, reminder fields. Update `list_tasks()` to build dynamic query with search (plainto_tsquery), filters (AND composition), sort, pagination. Return `total_count`, `page`, `total_pages` in response.
  - **Done when**: `add_task` with priority=P1, tags=["work"], due_date, recurrence_rule="weekly", reminder_minutes=30 creates correct task. `list_tasks` with search="meeting" + priority=P1 + sort_by=due_date + page=1 returns filtered, sorted, paginated results.

---

### Phase 2: Event-Driven Layer (show Kafka events working)

- [ ] V5-05 🚨 MUST — Create event emitter module `backend/events/`
  - **Agent**: Event-Driven Architecture | **Time**: ⏰ 30 min
  - **What**: Create `backend/events/__init__.py`, `backend/events/schemas.py` (TaskEvent dataclass with event_id UUID4, event_type, user_id, task_id, data dict, schema_version="1.0", timestamp ISO8601 UTC), `backend/events/transport.py` (DaprTransport class using httpx POST to `http://localhost:3500/v1.0/publish/task-pubsub/task-events` when `USE_DAPR=true`, KafkaTransport class using aiokafka when `USE_DAPR=false`, factory function `get_transport()`), `backend/events/emitter.py` (emit_event function: builds TaskEvent, calls transport.publish, catches errors with 3x retry, logs failures but never raises — fire-and-forget). Wire `emit_event()` calls into MCP tools `add_task`, `update_task`, `complete_task`, `delete_task` — ALWAYS after `session.commit()`.
  - **Done when**: Creating a task logs "Event published: task.created" to console. Event emission failure does not break the CRUD operation.

---

- [ ] V5-06 SHOULD — Create recurring task consumer `backend/consumers/recurring.py`
  - **Agent**: Event-Driven Architecture | **Time**: ⏰ 30 min
  - **What**: Create `backend/consumers/__init__.py`, `backend/consumers/recurring.py`. Consumer subscribes to `task-events` topic, filters for `event_type="task.completed"`. When received: check if `data.recurrence_rule` is set and task's `recurrence_depth < 1000`. If yes: create new task with same title/description/priority/tags/recurrence_rule, advance due_date by interval (daily=+1d, weekly=+7d, monthly=+1mo using `dateutil.relativedelta`), set `recurrence_parent_id` to parent task id, `recurrence_depth` = parent+1. Emit `task.created` event for new task. Track processed `event_id`s in a set for idempotency. Use Dapr subscription endpoint (`POST /dapr/subscribe` returns subscription list, Dapr invokes `POST /task-events` on the app).
  - **Done when**: Completing a recurring task auto-creates next occurrence with correct due_date and depth. Duplicate events are skipped.

---

### Phase 3: Dapr Integration (show sidecar pattern working)

- [ ] V5-07 🚨 MUST — Create Dapr component YAMLs `charts/todo-app/templates/dapr/`
  - **Agent**: Dapr Integration | **Time**: ⏰ 20 min
  - **What**: Create `charts/todo-app/templates/dapr/pubsub.yaml` (pubsub.kafka component named `task-pubsub` with broker/auth from secretKeyRef, conditional on `{{ if .Values.dapr.enabled }}`). Create `charts/todo-app/templates/dapr/statestore.yaml` (state.postgresql with connectionString from secretKeyRef). Create `charts/todo-app/templates/dapr/cron-binding.yaml` (bindings.cron named `reminder-cron`, `@every 1m`, direction=input). Create `charts/todo-app/templates/dapr/secretstore.yaml` (secretstores.kubernetes). Add Dapr sidecar annotations to `backend-deployment.yaml` template: `dapr.io/enabled`, `dapr.io/app-id`, `dapr.io/app-port` — all conditional on `{{ if .Values.dapr.enabled }}`.
  - **Done when**: `helm template` with `dapr.enabled=true` renders all 4 component YAMLs + sidecar annotations; with `dapr.enabled=false` renders none.

---

- [ ] V5-08 SHOULD — Create values-local.yaml with Dapr + Kafka config `charts/todo-app/values-local.yaml`
  - **Agent**: Dapr Integration | **Time**: ⏰ 15 min
  - **What**: Create `charts/todo-app/values-local.yaml` extending base values.yaml with: `dapr.enabled: true`, `dapr.appId: todo-backend`, `dapr.appPort: 8000`, `kafka.brokers: "kafka-cluster-kafka-bootstrap.kafka:9092"`, `kafka.authType: "none"` (Strimzi local has no auth), consumer deployments enabled. Set `imagePullPolicy: IfNotPresent` for all images. Set backend resources to requests 100m/128Mi, limits 500m/512Mi.
  - **Done when**: `helm template charts/todo-app -f charts/todo-app/values-local.yaml` renders correctly with Dapr annotations and Kafka broker URL.

---

### Phase 4: Local Deployment (get it running on Minikube)

- [ ] V5-09 🚨 MUST — Create deploy-local.sh and teardown-local.sh `scripts/`
  - **Agent**: Local Deployment | **Time**: ⏰ 30 min
  - **What**: Create `scripts/deploy-local.sh`: (1) Check Minikube running, start if not with `--memory=6144 --cpus=3 --driver=docker`. (2) `dapr init -k --runtime-version 1.13.0`, wait for dapr-system pods. (3) Install Strimzi operator via `kubectl apply -f https://strimzi.io/install/latest?namespace=kafka`, create namespace `kafka`, deploy 1-broker ephemeral Kafka cluster, wait for Ready. (4) Create topics: `task-events`, `reminders`, `task-updates` via KafkaTopic CRDs. (5) `eval $(minikube docker-env)` then `docker build -t todo-backend:local ./backend` and `docker build -t todo-frontend:local ./frontend`. (6) `helm upgrade --install todo-app charts/todo-app -f charts/todo-app/values-local.yaml --namespace todo-app --create-namespace --atomic --timeout 10m`. (7) Verify: `kubectl get pods -n todo-app` all Running. Create `scripts/teardown-local.sh`: helm uninstall, delete namespaces todo-app + kafka + dapr-system, stop Minikube. Both scripts: `set -euo pipefail`, echo each stage, add health check waits between stages.
  - **Done when**: `bash scripts/deploy-local.sh` from cold start → all pods Running within 10 minutes. `bash scripts/teardown-local.sh` cleans up completely.

---

- [ ] V5-10 SHOULD — Add consumer deployment template `charts/todo-app/templates/consumer-deployment.yaml`
  - **Agent**: Local Deployment | **Time**: ⏰ 15 min
  - **What**: Create a deployment template for the recurring task consumer. Reuses the backend image but with a different entrypoint: `python -m consumers.recurring`. Include Dapr sidecar annotations (same as backend). Set resources to requests 50m/64Mi, limits 200m/256Mi. Add readiness probe on `/healthz`. Conditional on `{{ if .Values.consumers.recurring.enabled }}`. Add corresponding service. Add `consumers.recurring.enabled: true` and `consumers.recurring.replicaCount: 1` to values-local.yaml.
  - **Done when**: `helm template` renders consumer deployment with Dapr sidecar; pod starts and subscribes to `task-events` topic.

---

### Phase 5: Cloud Deployment (show Oracle OKE attempt)

- [ ] V5-11 SHOULD — Create values-cloud.yaml `charts/todo-app/values-cloud.yaml`
  - **Agent**: Cloud Deployment | **Time**: ⏰ 15 min
  - **What**: Create cloud values overriding: `backend.image.repository: ghcr.io/shumaila/todo-backend`, `frontend.image.repository: ghcr.io/shumaila/todo-frontend`, `imagePullPolicy: Always`, `dapr.enabled: true`, `kafka.brokers` pointing to Redpanda Cloud, `kafka.authType: "password"`, `ingress.enabled: true` with `className: nginx` and TLS config, `backend.hpa.enabled: true` with min 1/max 3/target 70% CPU. Include comments explaining each override.
  - **Done when**: File exists with valid YAML; `helm template -f values-cloud.yaml` renders without errors.

---

- [ ] V5-12 NICE — Provision Oracle OKE cluster and deploy
  - **Agent**: Cloud Deployment | **Time**: ⏰ 45 min
  - **What**: Sign up for Oracle Cloud Always Free if not already. Create OKE cluster via OCI console (4 OCPUs, 24GB, 2 nodes). Install Dapr on cluster. Configure Redpanda Cloud Serverless (free tier) — create 3 topics, get SASL credentials. Create Kubernetes secrets for DB URL, API keys, Kafka credentials. Run `helm upgrade --install -f values-cloud.yaml --atomic`. If OKE unavailable: document the attempt with screenshots, create a "cloud-deployment-guide.md" showing the steps.
  - **Done when**: Either (a) app running on OKE with public URL + TLS, or (b) documented attempt with screenshots showing OKE cluster creation + Redpanda topics.

---

### Phase 6: CI/CD Pipeline

- [ ] V5-13 🚨 MUST — Create GitHub Actions CI/CD workflow `.github/workflows/deploy.yml`
  - **Agent**: CI/CD Pipeline | **Time**: ⏰ 20 min
  - **What**: Create workflow triggered on push to `main`. Jobs: (1) `lint-and-test`: checkout, setup Python 3.11, `pip install -r requirements.txt`, `ruff check backend/`, `ruff format --check backend/`, `pytest backend/tests/ --cov`. (2) `build-and-push` (needs lint-and-test): checkout, login to GHCR with `${{ secrets.GITHUB_TOKEN }}`, Docker Buildx setup, build backend image with `type=gha` cache, push to `ghcr.io/${{ github.repository_owner }}/todo-backend:{sha}` + `:latest`. Same for frontend. (3) `deploy` (needs build-and-push, if main branch): placeholder step that echoes "Deploy step — configure KUBECONFIG secret to enable" (since OKE may not be ready). All secrets via `${{ secrets.* }}`.
  - **Done when**: Workflow file valid YAML; push to main triggers pipeline; lint + test stage runs (even if tests fail, structure is correct).

---

- [ ] V5-14 NICE — Create rollback workflow `.github/workflows/rollback.yml`
  - **Agent**: CI/CD Pipeline | **Time**: ⏰ 10 min
  - **What**: `workflow_dispatch` trigger with input `revision` (string). Single job: configure kubectl, run `helm rollback todo-app ${{ github.event.inputs.revision }} --namespace todo-app --wait`.
  - **Done when**: File exists; workflow appears in GitHub Actions UI under "Run workflow" dropdown.

---

### Phase 7: Documentation & Polish

- [ ] V5-15 SHOULD — Update backend Dockerfile for consumers `backend/Dockerfile`
  - **Agent**: Feature Developer | **Time**: ⏰ 10 min
  - **What**: Add `aiokafka`, `httpx`, `croniter`, `python-dateutil` to `requirements.txt`. Ensure Dockerfile copies `events/` and `consumers/` directories. Default CMD remains `uvicorn main:app`. Consumer entrypoint set via Helm deployment command override.
  - **Done when**: `docker build -t todo-backend:local ./backend` succeeds with new dependencies included.

---

- [ ] V5-16 SHOULD — Update README with Phase V summary and demo instructions
  - **Agent**: Feature Developer | **Time**: ⏰ 15 min
  - **What**: Add "Phase V: Advanced Cloud Deployment" section to README with: feature list (priorities, tags, search, due dates, recurring, reminders), architecture diagram (link to mermaid in spec), quick start commands (`bash scripts/deploy-local.sh`), screenshots placeholder, link to spec/plan/tasks. Add "Demo Flow" subsection showing the end-to-end journey: create task with P1 priority + tags + weekly recurrence → complete it → see next occurrence auto-created → see event in Kafka topic.
  - **Done when**: README has Phase V section with clear demo instructions a judge can follow.

---

## Dependency Graph

```
V5-01 ─┐
V5-02 ─┤ (all migrations independent of each other)
V5-03 ─┘
   ↓
V5-04 (MCP tools need all migrations done)
   ↓
V5-05 (events need MCP tools to wire into)
   ↓
V5-06 (consumer needs event schemas)
   │
   ├── V5-07 (Dapr YAMLs independent of code)
   ├── V5-08 (values-local needs V5-07)
   │
   ↓
V5-09 (deploy script needs V5-07 + V5-08 + images)
V5-10 (consumer deployment needs V5-06 + V5-07)
   ↓
V5-11 (cloud values independent)
V5-12 (cloud deploy needs V5-11)
   │
V5-13 (CI/CD independent — can do anytime)
V5-14 (rollback needs V5-13)
   │
V5-15 (Dockerfile — do before V5-09)
V5-16 (README — do last)
```

## Parallel Opportunities

- **Batch 1** (⏰ simultaneous): V5-01 + V5-02 + V5-03 (all migrations)
- **Batch 2** (after migrations): V5-04 (MCP tools) + V5-07 (Dapr YAMLs) + V5-13 (CI/CD)
- **Batch 3** (after MCP tools): V5-05 (events) + V5-08 (values-local) + V5-15 (Dockerfile)
- **Batch 4** (after events): V5-06 (consumer) + V5-09 (deploy script) + V5-11 (cloud values)
- **Batch 5** (final): V5-10 + V5-12 + V5-14 + V5-16

## Critical Path (MUST items only — ~3 hours)

```
V5-01 (15m) → V5-02 (20m) → V5-03 (30m) → V5-04 (45m) → V5-05 (30m) → V5-07 (20m) → V5-09 (30m) → V5-13 (20m)
Total: ~3.5 hours for all MUST items
```
