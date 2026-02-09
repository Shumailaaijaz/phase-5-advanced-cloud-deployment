# Research: Phase V — Advanced Cloud Deployment

**Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## R1: Priority Enum Migration Strategy

**Decision**: Migrate existing free-text priority ("Low"/"Medium"/"High") to 4-level enum (P1-P4) via Alembic CASE mapping.

**Rationale**: A 4-level system (Critical/High/Medium/Low) is industry standard (JIRA, Linear, Asana). Using P1-P4 shorthand is concise for chatbot interactions and sortable alphabetically.

**Alternatives Considered**:
- Integer priority (1-4): Rejected — less readable in API responses and chatbot messages
- Keep 3-level text: Rejected — no "Critical" level, limits expressiveness
- PostgreSQL ENUM type: Rejected — harder to modify later; VARCHAR with CHECK constraint is more flexible

---

## R2: Tag Storage Pattern (Many-to-Many)

**Decision**: Separate `tag` table + `task_tag` junction table with `UNIQUE(user_id, name)` on tags.

**Rationale**: Normalized storage prevents tag name duplication per user, enables efficient tag listing with counts, and supports future features (tag colors, descriptions). Junction table with composite PK prevents duplicate task-tag associations.

**Alternatives Considered**:
- Array column on task (`tags TEXT[]`): Rejected — no referential integrity, hard to query tag counts, PostgreSQL-specific
- JSON array column: Rejected — same problems as array, plus no indexing for filter queries
- Single tags table without user scoping: Rejected — violates user isolation (constitution 2.6)

---

## R3: Full-Text Search Implementation

**Decision**: PostgreSQL `TSVECTOR` column with GIN index + auto-update trigger, queried via `plainto_tsquery`.

**Rationale**: Native PostgreSQL FTS is zero-cost (no external service), performant with GIN index for 10K+ tasks, and supports ranking. `plainto_tsquery` prevents SQL injection via raw tsquery syntax.

**Alternatives Considered**:
- ILIKE pattern matching: Rejected — O(n) scan, no relevance ranking, poor performance at scale
- External search service (Elasticsearch/Meilisearch): Rejected — additional infrastructure, cost, and complexity for a chatbot with < 10K tasks per user
- `pg_trgm` trigram extension: Viable for fuzzy matching but TSVECTOR is better for word-based search on natural language task titles

---

## R4: Due Date Type Migration (VARCHAR → TIMESTAMPTZ)

**Decision**: ALTER COLUMN from VARCHAR to `TIMESTAMP WITH TIME ZONE` with data conversion via CASE.

**Rationale**: TIMESTAMPTZ enables native date arithmetic (reminder calculation), range queries (`due_before`/`due_after`), and correct timezone handling. The existing VARCHAR "YYYY-MM-DD" strings are safely convertible.

**Alternatives Considered**:
- Keep VARCHAR and parse in Python: Rejected — no DB-level range queries, timezone bugs
- DATE type (without time): Rejected — reminders need hour-level precision
- Two columns (date + timezone): Rejected — TIMESTAMPTZ handles this natively

---

## R5: Recurrence Rule Format

**Decision**: Simple string enum (`daily`/`weekly`/`monthly`) + 5-field cron expressions, stored as VARCHAR(100).

**Rationale**: Simple intervals cover 90% of use cases. Cron expressions handle complex schedules (weekdays only, specific hours). The `croniter` Python library parses both formats reliably.

**Alternatives Considered**:
- RFC 5545 RRULE (iCalendar): Rejected — over-engineered for a todo app; complex parsing for minimal benefit
- Integer interval in minutes: Rejected — "monthly" isn't a fixed number of minutes
- Separate table for recurrence rules: Rejected — over-normalized; rule is 1:1 with task

---

## R6: Kafka Transport — Dapr vs Direct aiokafka

**Decision**: Dual transport with `USE_DAPR` environment variable toggle. Default `true` (Dapr HTTP), fallback `false` (direct aiokafka).

**Rationale**: Dapr abstraction is a constitution non-negotiable (2.1). Direct aiokafka fallback ensures hackathon resilience (constitution 2.5) when Dapr sidecar is unavailable during development.

**Alternatives Considered**:
- Dapr only (no fallback): Rejected — violates constitution 2.5 (fallbacks for everything)
- Direct aiokafka only: Rejected — violates constitution 2.1 (Dapr abstraction is sacred)
- Redis Streams instead of Kafka: Viable but Kafka is the spec requirement; Redis can be swapped via Dapr YAML

---

## R7: Cloud Kubernetes Provider

**Decision**: Oracle OKE always-free tier as primary. Azure AKS ($200/30d) as fallback #1. Google GKE ($300/90d) as fallback #2.

**Rationale**: OKE always-free provides 4 OCPUs + 24GB RAM with no time limit — the only truly free K8s option. AKS and GKE have generous but time-limited credits.

**Alternatives Considered**:
- AWS EKS: Rejected — no free tier for EKS control plane ($0.10/hr)
- DigitalOcean K8s: Rejected — no free tier
- Self-hosted K3s on Oracle VM: Viable but OKE is managed, reducing operational overhead

---

## R8: Managed Kafka Provider

**Decision**: Redpanda Cloud Serverless (free tier) for cloud. Strimzi operator on Minikube for local.

**Rationale**: Redpanda Cloud Serverless is Kafka-compatible, free, requires no Zookeeper, and has a generous free tier. Strimzi provides a lightweight self-hosted option for local development.

**Alternatives Considered**:
- Confluent Cloud: Rejected — free tier limited to 30 days, then expensive
- Amazon MSK Serverless: Rejected — no free tier
- Upstash Kafka: Viable alternative but less Kafka-compatible than Redpanda
- Self-hosted Redpanda on K8s: Viable but more resource-intensive than Strimzi for local dev

---

## R9: Monitoring Stack Selection

**Decision**: kube-prometheus-stack (Prometheus + Grafana) + Loki + Promtail. Dashboards as ConfigMaps.

**Rationale**: Industry-standard K8s observability stack. Helm chart available (`kube-prometheus-stack`). Loki provides log aggregation without Elasticsearch overhead. ConfigMap dashboards survive pod restarts.

**Alternatives Considered**:
- Cloud-native monitoring (OCI Monitoring, Azure Monitor): Rejected — vendor lock-in, harder to develop locally
- Datadog/New Relic: Rejected — expensive, overkill for hackathon
- Just Prometheus without Grafana: Rejected — no visualization; Grafana adds 128Mi, worth it

---

All NEEDS CLARIFICATION items resolved. No blockers for Phase 1.
