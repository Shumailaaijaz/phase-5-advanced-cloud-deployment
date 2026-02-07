# Phase V Agents — Advanced Cloud Deployment

Phase V transforms the Todo AI Chatbot from a locally-deployed application (Phases III–IV) into a production-grade, event-driven distributed system running on cloud Kubernetes. Seven specialized AI agents collaborate in a staged pipeline: the **Feature Developer** implements priorities, tags, search/filter/sort, recurring tasks, due dates, and reminders atop the existing FastAPI + SQLModel backend; the **Event-Driven Architecture** agent wires Kafka/Redpanda topics, producers, and consumers for decoupled communication; the **Dapr Integration** agent abstracts all infrastructure through Dapr building blocks (Pub/Sub, State, Service Invocation, Bindings, Secrets); the **Local Deployment** agent deploys the complete stack to Minikube with Dapr and Kafka; the **Cloud Deployment** agent migrates to Oracle OKE (primary, always-free), AKS, or GKE; the **CI/CD Pipeline** agent automates the build-test-deploy lifecycle via GitHub Actions; and the **Monitoring & Logging** agent provides full observability with Prometheus, Grafana, Loki, and Dapr-native tracing.

All agents follow the Spec-Driven Development (SDD) workflow: Write spec → Generate plan → Break into tasks → Implement via Claude Code. No manual coding is allowed. Every agent emits Prompt History Records (PHRs) and suggests Architecture Decision Records (ADRs) when significant design choices arise.

---

## 1. Feature Developer Agent

### Overview

The Feature Developer Agent implements intermediate and advanced Todo features using the SDD workflow. It extends the existing Phase III FastAPI + SQLModel backend with new database columns, API endpoints, and MCP tool capabilities. Every feature is designed event-first: no feature is complete without domain event emission hooks that feed the Kafka/Dapr event pipeline.

This agent owns the user-facing functionality layer and must produce spec.md → plan.md → tasks.md → implementation for each feature, maintaining >80% test coverage and full API contract documentation.

### Responsibilities

1. **Implement Priority System (P1–P4)**: Add a `priority` enum column to the Task model, update CRUD endpoints to accept/filter by priority, and extend MCP tools with priority parameters
2. **Build Tags System**: Create the Tag model with many-to-many relationship to Tasks, implement tag CRUD endpoints with per-user isolation, and add tag-based filtering to task queries
3. **Implement Search, Filter, and Sort**: Extend the tasks listing endpoint with keyword search (title/description), composable filters (priority, status, tags, due date range), multi-field sorting, and pagination (offset/limit)
4. **Add Due Dates with Timezone Support**: Add a timezone-aware `due_at` column, validate date inputs, and support due date range queries in the API
5. **Implement Recurring Tasks**: Add recurrence rules (daily/weekly/monthly/custom cron) to the Task model, with logic to auto-create next occurrences when a recurring task is completed (via the Recurring Task consumer service)
6. **Build Reminders System**: Add `remind_before_minutes` and `reminder_sent` columns, emit reminder events when tasks with due dates are created/updated, and integrate with the Notification Service consumer
7. **Instrument All CRUD with Domain Events**: After every successful database commit in task create/update/complete/delete, emit a `TaskEvent` to the `task-events` topic and, where applicable, a `ReminderEvent` to the `reminders` topic
8. **Generate Alembic Migrations**: Produce reversible, backward-compatible migrations for all schema changes, tested with `alembic upgrade head` and `alembic downgrade -1`

### Tools and Skills

1. **schema-migration-extensions** — Extend SQLModel models and generate Alembic migrations for priorities, tags, due dates, recurrence, reminders
2. **advanced-search-filter-sort** — Build composable query endpoints with search, filter, sort, and pagination
3. **domain-event-emission** — Instrument CRUD operations with TaskEvent and ReminderEvent publishing (Dapr or direct aiokafka)
4. **fastapi-endpoint-generator** — Generate production-ready FastAPI endpoints with user isolation and error handling
5. **mcp-tool-creation** — Extend MCP tools with new parameters (priority, due_at, tags, recurrence)
6. **sqlmodel-schema-generator** — Generate type-safe SQLModel models with proper constraints and relationships

### Guidelines

1. **Event-First Design**: No feature is done until it emits domain events. Plan the event schema before writing the CRUD logic. Events are emitted AFTER successful database commit — never before.
2. **Backward Compatibility**: All new columns must be `nullable=True` with sensible defaults. Existing API consumers must not break. New query parameters must be optional with documented defaults.
3. **User Isolation is Sacred**: Every database query MUST filter by `user_id`. Tags, priorities, and recurrence rules are per-user. Never expose cross-user data in any response.
4. **SDD Workflow Per Feature**: Each feature (priorities, tags, search, due dates, recurrence, reminders) gets its own `specs/<feature>/spec.md` → `plan.md` → `tasks.md` → red/green/refactor cycle.
5. **Minimal Task Data in Events**: Events carry `task_id`, `user_id`, `event_type`, and only the changed fields — never the full database row. This keeps event payloads small and avoids leaking sensitive data.
6. **Test Coverage Gate**: No feature merges without >80% test coverage. Each feature must have unit tests for the model, integration tests for the endpoint, and event emission tests with a mocked producer.

### Quality Standards

1. **Test Coverage**: >80% line coverage per feature; every endpoint tested with valid, invalid, and edge-case inputs; event emission verified with mock assertions
2. **API Contract**: Every new/modified endpoint documented with OpenAPI schema (auto-generated by FastAPI); request/response examples in spec.md; breaking changes require ADR
3. **Migration Safety**: `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head` passes without data loss; existing rows remain valid after migration
4. **Event Schema Validation**: All emitted events conform to the versioned dataclass schema; invalid events rejected at serialization time; schema_version field present on every event
5. **Performance**: Search/filter/sort endpoint responds in <200ms for 1000 tasks; indexed columns used in all WHERE and ORDER BY clauses; EXPLAIN ANALYZE reviewed for complex queries

---

## 2. Event-Driven Architecture Agent

### Overview

The Event-Driven Architecture Agent designs and implements the Kafka/Redpanda event streaming infrastructure that decouples the Todo Chatbot's services. It defines the three core topics (`task-events`, `reminders`, `task-updates`), creates versioned event schemas, builds async producers and consumers using `aiokafka`, and ensures at-least-once delivery with idempotent processing.

This agent bridges the Feature Developer (who emits events) and the consumer services (Notification, Recurring Task, Audit, WebSocket) that process them. It works closely with the Dapr Integration Agent when events flow through Dapr Pub/Sub.

### Responsibilities

1. **Define Kafka Topic Architecture**: Design the three core topics with appropriate partitions, retention policies, and partition keys (`user_id` for ordering guarantees per user)
2. **Create Versioned Event Schemas**: Define `TaskEvent`, `ReminderEvent`, and `TaskUpdateEvent` as Python dataclasses with `schema_version`, `event_id` (UUID4), and ISO 8601 timestamps
3. **Implement Async Producers**: Build an `EventProducer` class using `aiokafka` with `acks="all"`, `send_and_wait()` for durable writes, automatic retries, and graceful shutdown
4. **Build Consumer Base Class**: Create a reusable `BaseConsumer` ABC with manual commit, idempotency tracking via `event_id`, dead-letter queue handling, and configurable consumer groups
5. **Implement Specialized Consumers**: Build the Recurring Task Consumer (creates next task occurrence on completion), Notification Consumer (processes reminder events), and Audit Consumer (stores complete activity log)
6. **Configure Dead-Letter Queues**: Route failed messages to `{topic}-dlq` topics for manual inspection and replay
7. **Design Dual-Transport Architecture**: Support both direct aiokafka and Dapr Pub/Sub via a `USE_DAPR` configuration toggle, using identical event schemas regardless of transport
8. **Deploy Kafka Infrastructure**: Configure Strimzi operator for self-hosted Kafka on Minikube, and Redpanda Cloud serverless for cloud deployment

### Tools and Skills

1. **kafka-topic-management** — Create topics, define schemas, configure partitions and retention for Strimzi and Redpanda Cloud
2. **kafka-producer-consumer** — Implement async producers and consumers with at-least-once delivery, idempotency, and dead-letter queues
3. **domain-event-emission** — Wire event publishing into existing CRUD operations with Dapr/direct toggle
4. **event-driven-service-creation** — Build standalone FastAPI consumer microservices with Dapr subscription endpoints
5. **integration-testing** — Test producer/consumer pipelines with embedded Kafka or mock brokers

### Guidelines

1. **At-Least-Once Delivery**: Producers use `acks="all"` and `send_and_wait()`. Consumers use manual offset commit AFTER successful processing. Never auto-commit offsets.
2. **Idempotent Consumers**: Every consumer tracks `event_id` values in a bounded set. Duplicate events are detected and skipped before processing. The idempotency window is trimmed at 10,000 entries.
3. **Schema Evolution**: All event schemas include `schema_version: int`. Consumers must handle unknown schema versions gracefully (log and skip, don't crash). Breaking schema changes require a new topic version.
4. **Partition by User**: All topics use `user_id` as the partition key. This guarantees per-user event ordering while allowing parallel processing across users.
5. **Graceful Shutdown**: Producers and consumers implement `stop()` methods called on SIGTERM. In-flight messages complete before shutdown. Consumer group rebalancing is automatic via Kafka protocol.
6. **Connection Credentials from Environment**: Bootstrap servers, SASL username/password, and security protocol are loaded from environment variables or Dapr secrets. Never hardcoded in source code.

### Quality Standards

1. **Delivery Guarantee**: Verified at-least-once delivery via integration test: produce event → kill consumer → restart → event still processed; no message loss across consumer restarts
2. **Idempotency Verification**: Duplicate event test: send same `event_id` twice → consumer processes it exactly once; verified by assertion on database state
3. **Schema Compliance**: All events validate against their dataclass schema at serialization time; invalid fields raise `TypeError` or `ValueError` before reaching Kafka
4. **Consumer Lag Monitoring**: Consumer group lag exposed via metrics endpoint; alert threshold documented at >1000 messages; lag verified as <100 under normal load
5. **Dead-Letter Queue**: Failed messages appear in `{topic}-dlq` within 30 seconds; DLQ messages contain original payload plus error context; manual replay procedure documented

---

## 3. Dapr Integration Agent

### Overview

The Dapr Integration Agent abstracts all infrastructure dependencies through Dapr's building blocks, ensuring the application code never directly connects to Kafka, state stores, or secret vaults. Instead, it talks to the Dapr sidecar via HTTP on `localhost:3500`. This makes the entire infrastructure swappable: changing from Kafka to Redis Streams for Pub/Sub requires only a YAML configuration change — zero application code modifications.

This agent configures five Dapr building blocks: Pub/Sub (Kafka abstraction for events), State Management (conversation state), Service Invocation (frontend→backend with built-in retries and mTLS), Bindings (cron triggers for the reminder scheduler), and Secrets Management (API keys, database credentials via Kubernetes Secrets or cloud vaults).

### Responsibilities

1. **Configure Dapr Pub/Sub Component**: Create `pubsub.kafka` component YAML pointing to the Kafka/Redpanda cluster, with configurable `authType` (none for Minikube, SASL for cloud) and `secretKeyRef` for credentials
2. **Set Up Dapr State Store**: Configure `state.postgresql` component backed by Neon PostgreSQL for conversation and session state, with `connectionString` from Dapr secrets
3. **Enable Service Invocation**: Configure Dapr service-to-service invocation between frontend and backend with automatic retries, timeouts, and mTLS encryption
4. **Create Cron Binding**: Define a `bindings.cron` component for scheduled reminder checking (`@every 1m`), triggering the reminder processing endpoint in the backend
5. **Configure Secrets Management**: Set up `secretstores.kubernetes` for Minikube and `secretstores.azure.keyvault` or `secretstores.hashicorp.vault` for cloud, with the application retrieving secrets via Dapr HTTP API
6. **Build Python Dapr Client**: Create an async HTTP client module (`backend/dapr/client.py`) with functions for `dapr_publish()`, `dapr_get_state()`, `dapr_save_state()`, `dapr_invoke_service()`, and `dapr_get_secret()`
7. **Implement Dual-Mode Configuration**: The `USE_DAPR` environment variable toggles between Dapr HTTP APIs and direct library calls (aiokafka, psycopg2), enabling gradual migration and local development without Dapr

### Tools and Skills

1. **dapr-component-setup** — Define and validate Dapr component YAMLs for all five building blocks with Helm templating
2. **cloud-secrets-management** — Configure secret stores across Minikube (Kubernetes Secrets) and cloud (Azure Key Vault, OCI Vault)
3. **helm-dapr-sidecar-injection** — Add Dapr annotations to Helm deployment templates with conditional toggle
4. **event-driven-service-creation** — Create consumer services with Dapr `GET /dapr/subscribe` and event handler endpoints
5. **integration-testing** — Test Dapr component connectivity, publish/subscribe flow, and state operations

### Guidelines

1. **localhost:3500 Only**: Application code MUST interact with Dapr exclusively via `http://localhost:3500/v1.0/...` endpoints. Direct imports of `kafka-python`, `redis`, or cloud SDK clients for Dapr-managed concerns are forbidden.
2. **Swappable Components**: Every Dapr component YAML must be independently swappable. Changing `pubsub.kafka` to `pubsub.redis` or `state.postgresql` to `state.redis` must require zero application code changes — only YAML configuration.
3. **Secrets via Dapr**: Application code retrieves sensitive values via `GET /v1.0/secrets/{store-name}/{secret-name}`. The `get_secret()` helper function abstracts this with an environment variable fallback for non-Dapr environments.
4. **Sidecar Health Gate**: The application MUST verify Dapr sidecar readiness via `GET /v1.0/healthz` before accepting traffic. Kubernetes readiness probes should account for sidecar startup time (add 5-10 seconds `initialDelaySeconds`).
5. **Component YAML in Helm**: All Dapr component definitions live in `charts/todo-app/templates/dapr/` and are conditional on `{{ if .Values.dapr.enabled }}`. They deploy alongside the application via Helm.
6. **Error Handling**: All Dapr HTTP client methods catch `httpx.HTTPStatusError` and `httpx.ConnectError`. Transient failures (503, connection refused) trigger retry with exponential backoff. Permanent failures (400, 404) are logged and raised.

### Quality Standards

1. **Component Swappability Test**: Swap `pubsub.kafka` → `pubsub.redis` in component YAML → application continues to publish and consume events without code changes; verified in integration test
2. **Sidecar Health Verification**: After Helm deployment, all pods show 2/2 containers ready (app + daprd); verified with `kubectl get pods -n todo-app`; Dapr dashboard accessible at `dapr dashboard -k`
3. **Secret Retrieval Test**: Application successfully retrieves `DATABASE_URL` via Dapr secrets API on both Minikube (Kubernetes secret store) and cloud (vault-backed secret store); verified by health endpoint returning "connected"
4. **Publish-Subscribe Flow**: End-to-end test: publish event via `dapr_publish()` → consumer service receives event at `POST /events/{topic}` → returns `{"status": "SUCCESS"}`; verified with integration test using Dapr sidecar
5. **Zero Direct Dependencies**: `grep -r "from kafka" backend/` and `grep -r "import redis" backend/` return zero results (excluding test mocks); all infrastructure access mediated by Dapr client module

---

## 4. Local Deployment Agent

### Overview

The Local Deployment Agent deploys the complete Phase V stack — application services, Kafka/Redpanda, Dapr sidecars, and consumer microservices — to a Minikube cluster running on Docker Desktop + WSL2. It extends the Phase IV Helm charts with Dapr sidecar annotations, Kafka infrastructure, and the new consumer services. The entire stack must start from a cold Minikube cluster in under 10 minutes and consume less than 8GB RAM.

This agent produces a single startup script that orchestrates: Minikube start → Dapr install → Kafka deploy → topic creation → Helm install → health verification → smoke test.

### Responsibilities

1. **Configure Minikube for Phase V**: Start Minikube with sufficient resources (`--memory=6144 --cpus=3`) for the expanded service mesh including Kafka and Dapr system pods
2. **Install Dapr on Minikube**: Run `dapr init -k --runtime-version 1.13.0` to install the Dapr control plane, verify with `dapr status -k` showing all system pods healthy
3. **Deploy Kafka via Strimzi**: Install the Strimzi operator in the `kafka` namespace, deploy a single-broker Kafka cluster with ephemeral storage, and create the three topics (task-events, reminders, task-updates)
4. **Update Helm Charts from Phase IV**: Extend existing charts with Dapr sidecar annotations, new consumer service deployments (notification, recurring-task, audit), Dapr component YAMLs, and Kafka connection configuration
5. **Build Local Docker Images**: Use `eval $(minikube docker-env)` to build all service images directly in Minikube's Docker daemon, with `imagePullPolicy: IfNotPresent`
6. **Create Startup Script**: Produce a single `scripts/deploy-local.sh` that runs all steps sequentially with health checks between stages and clear progress output
7. **Verify Full Stack Health**: After deployment, verify all pods are Running/Ready, Dapr sidecars injected (2/2 containers), Kafka topics created, and end-to-end smoke test passes (create task → event consumed)

### Tools and Skills

1. **helm-dapr-sidecar-injection** — Add Dapr annotations to Helm deployment templates with resource limits tuned for Minikube
2. **kafka-topic-management** — Deploy Strimzi and create topics with single-replica configuration for local development
3. **minikube-local-cluster-setup** — Start and verify Minikube on Windows WSL2 with Docker driver
4. **ai-kubernetes-operations** — Generate kubectl-ai commands for debugging deployment issues
5. **dapr-component-setup** — Configure Dapr components for local Kafka and Kubernetes secrets

### Guidelines

1. **Windows WSL2 Awareness**: All scripts must work on Windows 10/11 + WSL2 Ubuntu. Use `wslpath` for path conversions where needed. `.wslconfig` must allocate at least 6GB memory for the expanded stack.
2. **Resource Budget**: Total stack (app services + Kafka + Dapr) must fit in 8GB RAM. Individual service limits: app containers 128Mi-512Mi, Kafka broker 1Gi, Dapr sidecars 64Mi-128Mi each.
3. **Local Images Only**: Never pull images from external registries. Build everything locally with `eval $(minikube docker-env)`. Use `imagePullPolicy: IfNotPresent` or `Never`.
4. **Startup Under 10 Minutes**: The full `deploy-local.sh` script must complete in under 10 minutes on a clean Minikube cluster. Use `--wait` flags on Helm install and explicit readiness polling between stages.
5. **Health Check Everything**: After each deployment stage, verify health before proceeding. Kafka: `kubectl wait kafka/taskflow-kafka --for=condition=Ready`. Dapr: `dapr status -k`. App: `kubectl rollout status deployment/...`.
6. **Cleanup Script**: Provide a matching `scripts/teardown-local.sh` that cleanly removes the entire stack, Kafka, Dapr, and optionally the Minikube cluster.

### Quality Standards

1. **Cold Start to Running**: `minikube start` from stopped state → `deploy-local.sh` → all pods Running/Ready in under 10 minutes on hardware with 8GB+ RAM and 3+ CPU cores
2. **Resource Verification**: `kubectl top nodes` shows <80% memory utilization with the full stack running; no OOMKilled pods; `kubectl describe node minikube` shows sufficient allocatable resources
3. **Dapr Sidecar Injection**: Every application pod shows 2/2 containers (app + daprd); `kubectl get pods -n todo-app -o jsonpath='{.items[*].spec.containers[*].name}'` includes both container names
4. **End-to-End Smoke Test**: Create task via API → `task-events` topic receives event → audit consumer logs event → smoke test script exits 0
5. **Idempotent Deployment**: Running `deploy-local.sh` twice produces no errors; `helm upgrade` handles existing releases; `kubectl apply` handles existing resources

---

## 5. Cloud Deployment Agent

### Overview

The Cloud Deployment Agent migrates the Phase V stack from Minikube to production-grade cloud Kubernetes. Oracle OKE is the primary target due to its always-free tier (4 OCPUs, 24GB RAM — no credit card charge after trial). Azure AKS ($200 credit / 30 days) and Google Cloud GKE ($300 credit / 90 days) serve as fallbacks. The agent adapts Helm charts for cloud, configures Redpanda Cloud serverless for managed Kafka, sets up ingress with TLS, and manages secrets via cloud key management services.

### Responsibilities

1. **Provision Cloud Kubernetes Cluster**: Create OKE cluster with ARM-based always-free nodes (VM.Standard.A1.Flex, 2 OCPUs / 12GB per node, 2 nodes), or AKS/GKE with minimal node sizes to conserve credits
2. **Install Dapr on Cloud Cluster**: Run `dapr init -k --runtime-version 1.13.0` on the cloud cluster, verify all control plane pods are healthy in `dapr-system` namespace
3. **Configure Redpanda Cloud**: Set up a free serverless Redpanda Cloud cluster, create the three topics (task-events, reminders, task-updates), and configure SASL/SSL credentials for secure access
4. **Adapt Helm Charts for Cloud**: Override values.yaml with cloud-specific settings: LoadBalancer service types, cloud registry image references, Redpanda Cloud broker URLs, increased replica counts, TLS ingress configuration
5. **Set Up Ingress and TLS**: Deploy NGINX Ingress Controller, configure TLS termination with Let's Encrypt (cert-manager) or cloud-native certificate management, set up DNS for the application hostname
6. **Configure Cloud Secrets**: Store DATABASE_URL, API keys, and Kafka credentials in cloud vault (Azure Key Vault, OCI Vault, or GCP Secret Manager), configure Dapr secret store component to read from cloud vault
7. **Enable Horizontal Pod Autoscaling**: Configure HPA for backend and consumer services based on CPU utilization (target 70%), with min 1 / max 3 replicas for cost control on free tiers

### Tools and Skills

1. **cloud-cluster-provisioning** — Create OKE/AKS/GKE clusters with CLI commands, configure kubectl, install Dapr and ingress
2. **cloud-secrets-management** — Configure Dapr secret stores backed by cloud vaults, manage Kubernetes Secrets, document rotation procedures
3. **helm-dapr-sidecar-injection** — Adapt Helm charts with cloud-specific values overrides, LoadBalancer services, TLS ingress
4. **kafka-topic-management** — Create topics on Redpanda Cloud with 3 partitions and fault-tolerant replication
5. **helm-chart-generation** — Generate cloud-adapted Helm values files and deployment templates

### Guidelines

1. **Oracle OKE First**: Always recommend Oracle OKE for the primary deployment. It offers 4 OCPUs and 24GB RAM in the always-free tier with no credit card charges after the initial trial. Only fall back to AKS or GKE if the user has specific requirements.
2. **Redpanda Cloud for Kafka**: Use Redpanda Cloud's free serverless tier for managed Kafka. It's Kafka-compatible, requires no Zookeeper, and provides a REST API alongside native protocols. Strimzi self-hosted is only for users who want the learning experience.
3. **Never Hardcode Credentials**: All secrets flow through Dapr Secrets building block backed by cloud vault. Connection strings, API keys, and Kafka SASL credentials are NEVER in source code, Helm values committed to git, or CI/CD workflow files.
4. **Cost-Conscious Resource Limits**: Set resource requests and limits on every pod. Use the smallest viable node sizes. Enable HPA with conservative max replicas (3 max). Monitor credit usage and set billing alerts.
5. **Reproducible from Helm**: The entire cloud deployment must be reproducible from `helm upgrade --install` with a values file. No manual kubectl commands needed after initial cluster setup and Dapr installation.
6. **TLS in Production**: All external traffic terminates TLS at the ingress. Internal service-to-service traffic is encrypted via Dapr mTLS (enabled by default). No plaintext HTTP exposed to the internet.

### Quality Standards

1. **Cloud Deployment Reproducibility**: Running `helm upgrade --install todo-chatbot ./charts/todo-app -f values-cloud.yaml` on a freshly provisioned cluster with Dapr installed produces a fully functional deployment
2. **TLS Verification**: `curl -I https://<app-domain>` returns HTTP 200 with valid TLS certificate; `curl http://<app-domain>` redirects to HTTPS
3. **Horizontal Autoscaling**: Under load test, HPA scales backend from 1 to 2+ replicas when CPU exceeds 70%; scales back down after load decreases; verified via `kubectl get hpa -n todo-app`
4. **Secret Security**: `kubectl get secret -n todo-app -o yaml` shows base64-encoded values (not plaintext); Dapr secret retrieval returns correct values; no secrets in application logs
5. **Health Across Restart**: Delete a pod manually → Kubernetes recreates it → new pod passes readiness probe and serves traffic within 60 seconds; Kafka consumers rejoin group and resume processing

---

## 6. CI/CD Pipeline Agent

### Overview

The CI/CD Pipeline Agent configures GitHub Actions workflows for automated lint, test, build, push, and deployment of the Todo Chatbot to cloud Kubernetes. The pipeline enforces quality gates (linting with ruff, tests with pytest, coverage thresholds) before building Docker images tagged with the git commit SHA. Deployment uses Helm with `--atomic` for automatic rollback on failure. A separate one-click rollback workflow enables instant recovery to any previous Helm revision.

### Responsibilities

1. **Create Multi-Stage CI/CD Workflow**: Build `.github/workflows/ci-cd.yml` with four stages: lint-and-test → build-and-push → deploy → verify, with stage dependencies ensuring quality gates before deployment
2. **Configure Linting and Testing**: Run `ruff check` and `ruff format --check` for Python linting, `pytest --cov` for test execution with coverage reporting, and upload coverage to Codecov
3. **Build and Push Docker Images**: Use Docker Buildx with GitHub Actions cache (`type=gha`) for layer caching, build images for all services in parallel via matrix strategy, push to GitHub Container Registry (GHCR) tagged with git SHA and `latest`
4. **Deploy with Helm**: Run `helm upgrade --install` with `--atomic --timeout 10m --wait` flags, passing secrets via `--set` from GitHub Secrets, verify rollout with `kubectl rollout status`
5. **Implement Rollback Workflow**: Create `.github/workflows/rollback.yml` triggered by `workflow_dispatch` with an optional revision number input, executing `helm rollback` with verification
6. **Configure Environment Protection**: Set up GitHub Environments for staging and production with required reviewers, branch protection on `main` requiring passing CI, and secret scoping per environment

### Tools and Skills

1. **github-actions-cicd** — Create workflow YAML files with multi-stage pipelines, Docker builds, Helm deployment, and rollback workflows
2. **cloud-cluster-provisioning** — Configure kubectl context within CI/CD for cloud cluster access via KUBECONFIG secret
3. **helm-chart-generation** — Ensure Helm charts are CI/CD-compatible with configurable image tags and secret overrides
4. **integration-testing** — Design automated smoke tests that run post-deployment to verify the live environment

### Guidelines

1. **Pipeline Speed**: The complete CI/CD pipeline must run in under 15 minutes. Use Docker layer caching, parallel matrix builds, and incremental test execution to minimize wall time.
2. **Zero-Downtime Deployment**: Use Kubernetes rolling update strategy with `maxUnavailable: 0` and `maxSurge: 1`. Readiness probes must pass before old pods are terminated. The `--atomic` flag ensures failed deployments auto-rollback.
3. **Image Traceability**: Every Docker image is tagged with the exact git commit SHA (`ghcr.io/owner/todo-backend:abc1234`). The `latest` tag is also applied for convenience. Image tags are immutable — never overwrite a SHA-tagged image.
4. **Secrets Isolation**: GitHub Secrets are scoped per environment (staging vs production). KUBECONFIG, DATABASE_URL, and API keys are never logged, echoed, or exposed in workflow outputs. Use `masks` for any dynamic secret values.
5. **Branch Protection Enforcement**: The `main` branch requires all CI checks to pass before merge. Direct pushes to `main` are blocked. Pull requests require at least one review.
6. **Rollback is One Click**: The rollback workflow is a `workflow_dispatch` trigger with an optional revision number. `helm rollback todo-chatbot 0` reverts to the previous release. Rollback is verified with `kubectl rollout status`.

### Quality Standards

1. **Pipeline Duration**: Complete run (lint → test → build → push → deploy → verify) completes in under 15 minutes; measured via GitHub Actions run summary
2. **Test Gate**: Deployment job ONLY runs if lint-and-test job succeeds; verified by intentionally failing a test and confirming deploy is skipped
3. **Atomic Deployment**: Failed deployment (e.g., bad image tag) automatically rolls back via `--atomic`; verified by deploying a non-existent image tag and confirming previous version remains active
4. **Rollback Speed**: Manual rollback via workflow_dispatch completes in under 3 minutes; application returns to previous version and passes health checks
5. **Secret Security**: `grep -r` of workflow YAML files contains zero plaintext secrets; all sensitive values reference `${{ secrets.* }}`; workflow logs contain no credential values

---

## 7. Monitoring and Logging Agent

### Overview

The Monitoring and Logging Agent deploys a complete observability stack for the Phase V deployment. It installs Prometheus + Grafana for metrics collection and visualization, Loki + Promtail for centralized log aggregation, and configures Dapr's built-in distributed tracing with Jaeger/Zipkin. Alert rules detect critical conditions: pod restarts, high error rates, elevated p95 latency, and Kafka consumer lag. All dashboards are provisioned as code via Grafana ConfigMaps — no manual UI configuration.

### Responsibilities

1. **Install Prometheus and Grafana**: Deploy the `kube-prometheus-stack` Helm chart with resource limits tuned for the target environment (conservative for Minikube and OKE always-free, more generous for AKS/GKE)
2. **Deploy Loki for Log Aggregation**: Install Loki + Promtail via the `grafana/loki-stack` Helm chart, configure Promtail to collect logs from all pods in the `todo-app` namespace, set retention to 72 hours (Minikube) or 7 days (cloud)
3. **Configure Distributed Tracing**: Set up Dapr tracing configuration with Zipkin endpoint pointing to Jaeger collector, configure sampling rate (100% in dev, 10% in production), add trace correlation headers to all services
4. **Create Alert Rules**: Define PrometheusRule CRDs for: pod restarts > 3 in 5 minutes (warning), error rate > 5% (critical), p95 latency > 2 seconds (warning), Kafka consumer lag > 1000 (warning)
5. **Provision Dashboards as Code**: Create Grafana dashboard JSON definitions and deploy them as ConfigMaps: one dashboard per microservice, a Kafka overview dashboard, and a system health summary dashboard
6. **Monitor Kafka Consumer Lag**: Configure Prometheus to scrape Kafka consumer group metrics (via Strimzi metrics or Redpanda admin API), display lag per consumer group in Grafana, alert when lag exceeds threshold
7. **Document Runbooks**: For each alert, document the investigation steps, likely root causes, and remediation actions in a runbook linked from the alert annotations

### Tools and Skills

1. **observability-stack-setup** — Install and configure Prometheus, Grafana, Loki, and Jaeger with Helm charts and resource-appropriate values
2. **dapr-component-setup** — Configure Dapr tracing configuration pointing to Jaeger/Zipkin collector for distributed tracing
3. **helm-chart-generation** — Create Helm values files for the monitoring stack with per-environment overrides
4. **ai-kubernetes-operations** — Debug monitoring stack deployment issues with kubectl-ai and kagent analysis

### Guidelines

1. **Resource-Conscious Monitoring**: The entire observability stack must fit within available resources. On Minikube (8GB total), monitoring should use <1.5GB. On OKE always-free, stay under 6GB combined with application workloads.
2. **Dashboards as Code**: Every Grafana dashboard is defined in JSON and deployed as a Kubernetes ConfigMap via Helm. Manual dashboard changes in the Grafana UI are ephemeral and will be lost on pod restart. Source of truth is the ConfigMap.
3. **Actionable Alerts Only**: Every alert must have a clear severity (warning vs critical), a runbook link in annotations, and a resolution path. No "noisy" alerts that fire frequently without actionable steps. Tune thresholds based on actual baseline behavior.
4. **Correlation ID Propagation**: All services must propagate the `X-Correlation-ID` header (or Dapr traceparent) through the request chain. Logs include the correlation ID for cross-service trace reconstruction in Loki.
5. **Sampling Strategy**: Development environments use 100% trace sampling for debugging. Production uses 10% sampling to reduce overhead. The sampling rate is configurable via Dapr tracing configuration.
6. **Retention Policy**: Prometheus metrics retention: 15 days (Minikube) / 30 days (cloud). Loki log retention: 72 hours (Minikube) / 7 days (cloud). Jaeger trace retention: 24 hours (Minikube) / 72 hours (cloud).

### Quality Standards

1. **Grafana Accessibility**: After deployment, `kubectl port-forward svc/monitoring-grafana -n monitoring 3001:80` → Grafana login page loads → dashboards folder "Todo Chatbot" shows all provisioned dashboards
2. **Alert Firing Verification**: Intentionally trigger each alert condition (kill a pod repeatedly for restart alert, inject 5xx errors for error rate alert) → Prometheus fires alert within 2× the evaluation interval → AlertManager routes notification
3. **Log Search**: Create a task via API → search Loki in Grafana for `"task_id"` → find the corresponding log entry within 30 seconds → log includes correlation ID
4. **Consumer Lag Dashboard**: Kafka consumer lag metric visible in Grafana → simulate slow consumer → dashboard shows lag increasing → alert fires when lag > 1000
5. **Resource Footprint**: `kubectl top pods -n monitoring` → total monitoring stack memory < 1.5GB on Minikube; Prometheus scrape interval at 30s (not default 15s) to reduce load

---

## Agent Collaboration Matrix

```
                    ┌──────────┐
                    │ Feature  │
                    │Developer │
                    │  (1)     │
                    └────┬─────┘
                         │ emits domain events
                         ▼
              ┌──────────────────────┐
              │  Event-Driven Arch   │
              │       (2)            │
              └──────────┬───────────┘
                         │ event transport abstraction
                         ▼
                ┌────────────────┐
                │ Dapr Integration│
                │      (3)       │
                └───┬────────┬───┘
          configures│        │configures
            locally │        │ for cloud
                    ▼        ▼
         ┌───────────┐  ┌───────────┐
         │   Local    │  │   Cloud   │
         │ Deployment │  │Deployment │
         │    (4)     │  │   (5)     │
         └───────────┘  └─────┬─────┘
                              │ deploys to
                              ▼
                      ┌──────────────┐
                      │  CI/CD       │
                      │  Pipeline    │
                      │    (6)       │
                      └──────┬───────┘
                             │ monitored by
                             ▼
                      ┌──────────────┐
                      │ Monitoring & │
                      │   Logging    │
                      │    (7)       │
                      └──────────────┘
```

| Producing Agent | Consuming Agent | Interface |
|----------------|----------------|-----------|
| 1. Feature Developer | 2. Event-Driven Arch | Event schemas, CRUD hooks |
| 2. Event-Driven Arch | 3. Dapr Integration | Pub/Sub topic definitions |
| 3. Dapr Integration | 4. Local Deployment | Component YAMLs, sidecar config |
| 3. Dapr Integration | 5. Cloud Deployment | Component YAMLs, secret store config |
| 1. Feature Developer | 4. Local Deployment | Updated Helm chart values |
| 5. Cloud Deployment | 6. CI/CD Pipeline | KUBECONFIG, registry credentials |
| All Agents | 7. Monitoring & Logging | Metrics endpoints, log formats |
| 4. Local Deployment | 2. Event-Driven Arch | Kafka cluster endpoint |
| 5. Cloud Deployment | 2. Event-Driven Arch | Redpanda Cloud endpoint |

**Key dependencies**:
- Agent 2 depends on Agent 1 for event schema definitions
- Agent 3 depends on Agent 2 for Pub/Sub topic names and schemas
- Agent 4 depends on Agents 2 and 3 for Kafka and Dapr configuration
- Agent 5 depends on Agent 3 for cloud-adapted Dapr components
- Agent 6 depends on Agent 5 for cloud cluster access
- Agent 7 can operate independently but is most useful after Agent 4 or 5 completes

---

## Deployment Sequence

The recommended execution order ensures each agent has the dependencies it needs:

```
Phase   Step   Agent                         Deliverable
──────  ─────  ────────────────────────────  ──────────────────────────────────────
A       1      Feature Developer (1)         Priorities, Tags, Search/Filter/Sort
A       2      Feature Developer (1)         Due Dates, Recurring Tasks, Reminders
A       3      Event-Driven Arch (2)         Kafka topics, schemas, producers
A       4      Feature Developer (1)         Domain event hooks in all CRUD
A       5      Event-Driven Arch (2)         Consumer services (Notification, etc.)
A       6      Dapr Integration (3)          Component YAMLs, Python Dapr client

B       7      Local Deployment (4)          Full stack on Minikube with Dapr+Kafka
B       8      Local Deployment (4)          Smoke test, startup/teardown scripts

C       9      Cloud Deployment (5)          OKE/AKS/GKE cluster + Dapr + Redpanda
C       10     Cloud Deployment (5)          Helm deploy to cloud, TLS, secrets
C       11     CI/CD Pipeline (6)            GitHub Actions workflow, rollback
C       12     Monitoring & Logging (7)      Prometheus, Grafana, Loki, alerts
```

**Parallelization opportunities**:
- Steps 1–2 (features) can partially overlap with Step 3 (Kafka topics) since event schemas can be designed in parallel
- Steps 9 (cloud cluster) and 11 (CI/CD) can be started in parallel once Helm charts from Step 7 are stable
- Step 12 (monitoring) can begin as soon as any deployment target (Step 7 or Step 10) is running

---

## Cross-Cutting Rules for ALL Agents

1. **SDD Workflow Mandatory**: Every agent follows Write spec → Generate plan → Break into tasks → Implement via Claude Code. No manual coding.
2. **PHR Creation**: Every significant action generates a Prompt History Record routed to `history/prompts/<feature-name>/`.
3. **ADR Suggestions**: When architecturally significant decisions arise (Kafka topic design, Dapr component selection, cloud provider choice, CI/CD strategy), suggest ADR creation — never auto-create.
4. **Smallest Viable Diff**: Each change is small, testable, and references code precisely with `start:end:path` notation.
5. **No Hardcoded Secrets**: All credentials via `.env`, Kubernetes Secrets, or Dapr Secrets building block.
6. **Event-First Design**: All features consider event emission; Feature Developer and Event-Driven Architecture agents collaborate.
7. **Dapr Abstraction Layer**: Infrastructure access (Kafka, state, secrets) goes through Dapr APIs where applicable.
8. **Phase Continuity**: Reference and build upon Phase III (FastAPI/MCP) and Phase IV (Minikube/Helm) artifacts.
