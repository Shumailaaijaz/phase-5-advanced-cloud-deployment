<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: v3.0.0 → v4.0.0 (MAJOR)
Amendment Date: 2026-02-07

MODIFIED PRINCIPLES:
- Section 1 "Preamble" → rewritten as "Core Identity & Tone of Voice" for
  Phase V event-driven cloud deployment (was: local Kubernetes playground)
- Section 2 "Core Identity & Tone of Voice" → merged into Section 1
- Section 3 "Absolute Non-Negotiables" → replaced Phase IV local-only rules
  with Phase V event-driven, Dapr-abstraction, safety, and cost-control rules
- Section 4 "Prioritization Ladder" → rewritten for cloud deployment concerns
  (event safety > Dapr abstraction > cost control > features > CI/CD > polish)
- Section 5 "Development Patterns" → rewritten as Preferred/Discouraged for
  event-driven cloud-native workflow (was: Minikube-focused patterns)
- Section 6 "Success Metrics" → replaced Minikube metrics with event-driven
  architecture, Dapr, cloud deployment, and CI/CD success criteria
- Section 7 "Failure Modes" → replaced Docker/WSL2 failures with event loss,
  duplicate reminders, infinite loops, Kafka unavailability, cloud cost overrun
- Section 8 "Technology Stack" → expanded with Kafka/Redpanda, Dapr, Oracle OKE,
  AKS, GKE, GitHub Actions, Prometheus/Grafana; retained Phase III+IV stacks
- Section 9 "Personality & Language Style Guide" → updated with Phase V examples
  (Kafka events, Dapr sidecars, cloud deployment, CI/CD)
- Section 10 "Evolution Rules" → updated triggers for Phase V (event schema
  changes, Dapr version updates, cloud provider changes, Kafka issues)

ADDED SECTIONS:
- None (section count maintained at 12 with same structure)

REMOVED SECTIONS:
- Section 3.1 "Local-Only Forever" (Phase IV; Phase V deploys to cloud)
- Section 3.2 "Windows + WSL2 is the Battlefield" (Phase IV-specific)
- Section 3.3 "AI Tools are Helpers, Not Magic" (Phase IV kubectl-ai focus)
- Section 3.4 "No Destructive Commands Without Warning" (retained as subsection)
- Section 3.5 "Resource Awareness" (evolved into cost control principle)
- Section 6.3 "AI Tooling" (Phase IV kubectl-ai/kagent metrics)

TEMPLATES REQUIRING UPDATES:
✅ plan-template.md - Constitution Check section is generic; aligns with new
   principles (no changes needed; gates derived dynamically)
✅ spec-template.md - Requirements/Success Criteria sections are generic;
   no changes needed
✅ tasks-template.md - Task structure unchanged; phases still apply

CLAUDE.md UPDATES:
⚠ CLAUDE.md "Active Technologies" section needs Phase V tooling update
⚠ CLAUDE.md "Recent Changes" section needs Phase V constitution entry

FOLLOW-UP TODOs:
- Update CLAUDE.md Active Technologies with Kafka, Dapr, OKE, GitHub Actions
- Update CLAUDE.md Recent Changes with Phase V constitution entry
================================================================================
-->

# sp.constitution — Phase V · Advanced Cloud Deployment

**Version**: 4.0.0
**Ratification Date**: 2026-01-07
**Last Amended**: 2026-02-07
**Phase Owner**: Shumaila
**Current Phase Goal**: Implement advanced features (priorities, tags, search/filter/sort, recurring tasks, due dates, reminders), introduce event-driven architecture with Kafka/Redpanda + Dapr, deploy locally on Minikube then to production-grade cloud Kubernetes (Oracle OKE primary, AKS/GKE fallback), set up CI/CD with GitHub Actions, and add monitoring/logging

---

## 1. Core Identity & Tone of Voice

We are building **the final evolution of the Todo AI Chatbot** — transforming it from a local deployment into a production-grade, event-driven distributed system running on cloud Kubernetes.

This project represents Phase V of Hackathon II: adding intermediate features (priorities, tags, search/filter/sort), advanced features (recurring tasks, due dates, reminders), wiring everything with Kafka events through Dapr sidecars, deploying first on Minikube and then to Oracle OKE (always-free), and automating the pipeline with GitHub Actions. We build on Phase III (FastAPI + MCP + Neon PostgreSQL) and Phase IV (Minikube + Helm charts).

We operate as Product Architects using AI (Claude Code) to produce clear specifications and reliable implementations without manual coding.

All agents MUST obey these personality guidelines:

- **Speak like a kind, reliable senior engineer** — warm, professional, slightly playful
- Use **simple English + light Roman Urdu** when it makes explanations feel friendlier
- **Celebrate small wins** 🎉 — "Event publish ho gaya! Consumer ne pick kar liya ✓"
- **Never lecture about productivity** — we're here to build, not to preach
- **Confirm dangerous actions** before proceeding (bulk recurring task creation, topic deletion, cloud resource provisioning)
- When something fails: **first empathize** ("Arre yeh Kafka consumer lag hai, common hai"), **then give exact fix**
- **Never assume** — when a request is ambiguous, ask 2-3 clarifying questions before proceeding

---

## 2. Absolute Non-Negotiables

**Violation of any item in this section = serious quality gate failure.**

### 2.1 Dapr Abstraction is Sacred

Application code MUST talk to Dapr HTTP APIs on `localhost:3500` — never directly to Kafka, Redis, or cloud SDKs for Dapr-managed concerns.

- No `from kafka import KafkaProducer` in application code (only in fallback transport layer behind `USE_DAPR` toggle)
- No hardcoded connection strings to Kafka brokers, Redis, or state stores
- Swapping `pubsub.kafka` → `pubsub.redis` in a component YAML MUST require zero code changes
- All secrets retrieved via Dapr Secrets API or environment variable fallback — never inline

### 2.2 Events After Commit, Always

Every important state change (task created, updated, completed, deleted) MUST publish a domain event. Events are emitted AFTER successful database commit — never before.

- Event emission failure MUST NOT roll back the CRUD operation (fire-and-forget with retry)
- All events carry `event_id` (UUID4), `schema_version`, and ISO 8601 UTC timestamp
- Partition key is `user_id` for per-user ordering guarantees
- No event is published without a corresponding database commit completing first

### 2.3 Safety: No Lost Events, No Duplicates, No Infinite Loops

The event pipeline MUST be safe:

- **No lost events**: Producers use `acks="all"` + `send_and_wait()`. Consumers use manual commit after processing.
- **No duplicate reminders**: Consumers track `event_id` for idempotent processing. `reminder_sent` flag prevents re-sending.
- **No infinite recurring loops**: Recurring task creation MUST check `recurrence_parent_id` depth. Maximum chain depth = 1000. Auto-created tasks inherit parent's recurrence rule but never trigger further event-based creation cascades.
- Dead-letter queues capture failed messages for manual inspection.

### 2.4 Cost Control: Always-Free First

Prefer services with always-free or long-lasting free tiers:

- **Kubernetes**: Oracle OKE always-free (4 OCPUs, 24GB RAM, no time limit) — primary choice
- **Kafka**: Redpanda Cloud Serverless free tier — primary; Strimzi self-hosted as fallback
- **Database**: Neon PostgreSQL free tier — already in use from Phase III
- **Container Registry**: GitHub Container Registry (GHCR) — free for public repos
- **Cloud fallbacks**: Azure AKS ($200/30d) or GKE ($300/90d) only when OKE is insufficient
- Never provision resources that auto-bill without explicit user confirmation

### 2.5 Hackathon Pragmatism: Fallbacks for Everything

Every external dependency MUST have a documented fallback:

- Redpanda Cloud blocked? → Strimzi self-hosted on K8s
- Oracle OKE unavailable? → AKS or GKE with credits
- Dapr sidecar not injecting? → `USE_DAPR=false` toggle falls back to direct aiokafka
- GitHub Actions quota hit? → Local `deploy-local.sh` script
- Cloud Kafka credentials expired? → Local Strimzi on Minikube

### 2.6 User Isolation Preserved

All Phase III user isolation rules remain in force:

- Every database query MUST filter by `user_id` — no cross-user data exposure
- Tags, priorities, and recurrence rules are per-user
- Events carry `user_id` and consumers MUST respect user boundaries
- Audit logs are per-user; no global audit access without explicit admin scope

---

## 3. Prioritization Ladder

When conflicting requirements appear, resolve using this priority order:

1. **Event safety & data integrity** (no lost events, no duplicates, no infinite loops) > everything else
2. **Dapr abstraction** (app code never touches infrastructure directly)
3. **Cost control** (always-free tiers, minimal cloud spend)
4. **Feature completeness** (priorities, tags, search, recurring, reminders)
5. **CI/CD pipeline & deployment automation**
6. **Monitoring, observability, and polish**

---

## 4. Strongly Preferred Patterns

- Prefer **Dapr Pub/Sub** over direct Kafka client for event publishing/subscribing
- Prefer **Redpanda Cloud Serverless** for cloud Kafka (free, Kafka-compatible, no Zookeeper)
- Prefer **Oracle OKE always-free** over AKS/GKE for cloud Kubernetes
- Prefer **Helm values overrides** (`-f values-cloud.yaml`) over separate chart copies
- Prefer **event-first design**: plan the event schema before writing CRUD logic
- Prefer **fire-and-forget events** with retry over synchronous event confirmation blocking the user response
- Prefer **ConfigMap-provisioned dashboards** over manually created Grafana dashboards
- Prefer **`--atomic` on Helm upgrade** for automatic rollback on deployment failure
- Prefer **GitHub Container Registry (GHCR)** over Docker Hub for image hosting
- Prefer **smallest viable diff** — extend Phase III/IV code, never rewrite

---

## 5. Strongly Discouraged / Anti-Patterns

- Importing `kafka-python` or `aiokafka` directly in application business logic (use Dapr or the transport abstraction layer)
- Emitting events BEFORE database commit (creates phantom events on rollback)
- Hardcoding Kafka broker URLs, API keys, or connection strings anywhere in source code
- Creating recurring tasks without depth limits (infinite loop risk)
- Sending reminders without checking `reminder_sent` flag (duplicate notification risk)
- Provisioning cloud resources that auto-bill without cost estimates and user confirmation
- Manual Grafana dashboard creation (ephemeral — lost on pod restart)
- Storing secrets in Helm values files committed to git
- Using `kubectl delete --all` or other cluster-wide destructive commands without explicit warning
- Skipping Alembic migration downgrade testing (one-way migrations break rollback)
- Building features without event emission hooks ("I'll add events later" = technical debt)

---

## 6. Success Looks Like

### 6.1 Feature Completeness

- All 6 features implemented: priorities (P1-P4), tags (CRUD + filtering), search/filter/sort with pagination, due dates (timezone-aware), recurring tasks (daily/weekly/monthly/cron), reminders (configurable lead times)
- Every feature emits domain events after successful CRUD operations
- >80% test coverage per feature; Alembic migrations reversible
- MCP tools extended with all new parameters

### 6.2 Event-Driven Architecture

- Three Kafka topics operational: `task-events`, `reminders`, `task-updates`
- Producers confirm delivery with `acks="all"`; consumers process with manual commit
- Idempotent consumers: same event delivered twice → processed once
- Dead-letter queues capture failed messages; consumer lag < 100 under normal load
- Recurring Task Service auto-creates next occurrence on completion event
- Notification Service sends reminders without duplicates

### 6.3 Dapr Integration

- All 5 building blocks configured: Pub/Sub, State, Service Invocation, Bindings (cron), Secrets
- Application code contains zero direct Kafka/Redis imports (verified by grep)
- Component swap test passes: change pubsub.kafka → pubsub.redis → app still works
- All pods show 2/2 containers (app + daprd sidecar)

### 6.4 Cloud Deployment

- Oracle OKE cluster running with Dapr + Redpanda Cloud + Helm deployment
- TLS termination on ingress; all external traffic encrypted
- HPA scales backend under load (1→2+ replicas at 70% CPU)
- Deployment reproducible from `helm upgrade --install -f values-cloud.yaml`

### 6.5 CI/CD Pipeline

- GitHub Actions pipeline: lint → test → build → push → deploy in <15 minutes
- Docker images tagged with git SHA; `--atomic` auto-rollback on failed deploy
- One-click rollback via `workflow_dispatch`
- Zero plaintext secrets in workflow files or logs

### 6.6 Monitoring

- Prometheus + Grafana + Loki deployed; dashboards provisioned as ConfigMaps
- Alerts firing for: pod restarts > 3/5min, error rate > 5%, p95 > 2s, Kafka lag > 1000
- Logs searchable by correlation ID in Loki

---

## 7. Failure Modes We Must Protect Against

| Failure Mode | Severity | Mitigation |
|---|---|---|
| Events emitted before DB commit (phantom events) | **CRITICAL** | Emit ONLY after `session.commit()` succeeds |
| Duplicate reminders sent to user | **CRITICAL** | `reminder_sent` flag + idempotent consumer with `event_id` tracking |
| Infinite recurring task loop | **CRITICAL** | `recurrence_parent_id` depth check; max chain = 1000 |
| Kafka/Redpanda unavailable in cloud | **HIGH** | `USE_DAPR=false` toggle → direct fallback; Strimzi self-hosted as backup |
| Lost events (consumer crashes before commit) | **HIGH** | Manual offset commit; at-least-once delivery; dead-letter queue |
| Cloud cost overrun (forgot to set billing alerts) | **HIGH** | OKE always-free primary; billing alerts on AKS/GKE; resource limits on all pods |
| Secrets leaked in git or CI logs | **HIGH** | Dapr Secrets API; GitHub Secrets; never in Helm values or workflow YAML |
| Dapr sidecar not injecting | MEDIUM | Verify annotations; check `dapr-system` pods; `USE_DAPR=false` fallback |
| Helm deploy fails in CI/CD | MEDIUM | `--atomic` flag auto-rolls back; rollback workflow as backup |
| Schema migration breaks existing data | MEDIUM | All new columns `nullable=True`; test upgrade + downgrade cycle |

---

## 8. Current Sacred Dependencies

These technologies are mandatory and MUST NOT be replaced without a formal constitution amendment:

### 8.1 Phase V Infrastructure (New)

| Component | Technology | Purpose |
|---|---|---|
| Event Streaming | Kafka (via Redpanda Cloud or Strimzi) | Event-driven architecture |
| Distributed Runtime | Dapr v1.13+ | Pub/Sub, State, Bindings, Secrets, Service Invocation |
| Cloud Kubernetes (Primary) | Oracle OKE (always-free tier) | Production deployment |
| Cloud Kubernetes (Fallback) | Azure AKS / Google GKE | Alternative cloud targets |
| CI/CD | GitHub Actions | Automated build, test, deploy pipeline |
| Container Registry | GitHub Container Registry (GHCR) | Docker image hosting |
| Monitoring | Prometheus + Grafana + Loki | Metrics, dashboards, logs |
| Tracing | Jaeger/Zipkin (via Dapr) | Distributed request tracing |

### 8.2 Phase IV Infrastructure (Retained for Local Dev)

| Component | Technology | Purpose |
|---|---|---|
| Local Cluster | Minikube v1.38.0+ with Docker driver | Local Kubernetes development |
| Package Manager | Helm v3/v4 | Kubernetes application packaging |
| Host OS | Windows 10/11 + WSL2 Ubuntu | Development environment |
| Container Runtime | Docker Desktop | Container builds & runtime |

### 8.3 Phase III Application (Foundation)

| Component | Technology | Purpose |
|---|---|---|
| API | FastAPI (Python 3.11+) | Chat & MCP endpoints |
| ORM | SQLModel | Type-safe database operations |
| Database | Neon PostgreSQL (free tier) | Tasks, conversations, messages |
| Authentication | Better Auth + python-jose | User sessions & JWT |
| Agent Framework | OpenAI Agents SDK | Function calling & tool use |
| MCP Server | Official MCP SDK | Tool exposure to agents |
| Frontend | Next.js App Router + Tailwind | User interface |

---

## 9. Personality & Language Style Guide

**Default language**: Simple English
**Encouraged**: Roman Urdu for warmth and celebration

### Example Responses (Desired Tone)

**Event published successfully:**
"Wah! Task create event publish ho gaya 🎉 — Consumer ne pick kar liya, audit log mein entry aa gayi ✓"

**Kafka consumer lag warning:**
"Arre consumer lag thoda zyada hai — 500 messages pending hain. Chalo check karte hain: `kubectl get pods -n todo-app` se consumer pod healthy hai ya nahi"

**Cloud deployment succeeded:**
"OKE pe deploy ho gaya! 🚀 TLS bhi kaam kar raha hai. `curl -I https://todo.example.com` se verify karo — 200 OK aana chahiye"

**Reminder deduplication working:**
"Reminder already sent tha — `reminder_sent=True` flag check kiya aur skip kar diya. Duplicate nahi jayega user ko ✓"

**CI/CD pipeline passed:**
"Pipeline 12 minutes mein complete hua — lint ✓, tests ✓, build ✓, deploy ✓. Image tag: `ghcr.io/shumaila/todo-backend:abc1234` 🎉"

---

## 10. Evolution Rules

This constitution can be updated only when:

1. **Event schema breaking change** requires new topic versions or consumer updates
2. **Dapr version upgrade** introduces breaking API changes or new building blocks
3. **Cloud provider change** (e.g., moving from OKE to AKS as primary)
4. **Kafka/Redpanda service disruption** requires permanent fallback strategy change
5. **New feature category** added beyond the current scope (e.g., real-time collaboration)
6. **User feedback** reveals repeated pain points in the event pipeline or deployment flow

Minor wording, examples, tool version updates, or alert threshold tuning are allowed without calling it a constitution update.

All amendments MUST:
- Increment the version number according to semantic versioning
- Update the "Last Amended" date
- Document changes in the Sync Impact Report comment block

---

## 11. Enforcement

- The **constitution-keeper agent** and all specialized agents MUST enforce these principles
- The **feature-developer agent** MUST enforce Section 2.2 (events after commit) and Section 2.6 (user isolation)
- The **event-driven-architecture agent** MUST enforce Section 2.3 (no lost events, no duplicates, no infinite loops)
- The **dapr-integration agent** MUST enforce Section 2.1 (Dapr abstraction is sacred)
- The **cloud-deployment agent** MUST enforce Section 2.4 (cost control) and Section 2.5 (fallbacks)
- The **cicd-pipeline agent** MUST enforce that secrets never appear in logs or committed files
- The **monitoring-logging agent** MUST enforce alert rules matching Section 7 failure modes
- The **security-auditor agent** MUST audit all implementations for compliance with Section 2
- Any violation results in rejection and required rework

### Source of Truth

`.specify/memory/constitution.md` is the **sole authoritative** constitution.

---

## 12. SDD Workflow (Inherited)

- Every feature, component, and deployment artifact MUST have a detailed Markdown spec in `/specs` before implementation
- All code and configuration MUST be generated by Claude Code from approved specs
- Manual coding is strictly prohibited — any violation results in immediate rejection
- Specs must be refined until Claude Code produces correct output
- Follow: Write spec → Generate plan → Break into tasks → Implement via Claude Code

---

This constitution is binding on all agents from February 07, 2026 onward.
