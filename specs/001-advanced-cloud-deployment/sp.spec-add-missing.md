# Phase V Spec -- Add Missing Features (Hackathon Crunch)

**Date**: February 07, 2026 | **Owner**: Shumaila
**Status**: Urgent | **Estimated Time**: < 2 hours
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Tasks**: [tasks.md](./tasks.md)

---

## 1. Objective

Complete the remaining Phase V gaps identified by cross-artifact analysis. The core features (priorities, tags, search/filter/sort, due dates, recurring tasks) and event infrastructure (emitter, transport, recurring consumer, Dapr YAMLs, CI/CD, deploy scripts) are done. What's missing: the Notification Service consumer for reminder delivery, an Audit Logger consumer, Dapr cron binding wiring, cloud deployment documentation with AKS/GKE fallback YAML, CI/CD pipeline verification, unit tests for Phase V features, and monitoring templates. All work reuses existing code and infrastructure -- no new architecture needed.

---

## 2. Missing Features to Add

### 2.1 Notification Service Consumer (Priority 1)
- **Why**: FR-012 requires exactly-once reminder delivery. The `check-reminders` cron endpoint publishes to the `reminders` topic, but no consumer processes those events.
- **How**: Create `backend/consumers/notification.py` -- FastAPI app with Dapr subscription to `reminders` topic. On `reminder.due` event: log the reminder, mark `reminder_sent=True` in DB. Track `event_id` for idempotency. Add deployment template to Helm chart.

### 2.2 Audit Logger Consumer (Priority 2)
- **Why**: Spec section 6 lists Audit Logger as a consumer. Provides event trail for debugging and judge demo.
- **How**: Create `backend/consumers/audit.py` -- subscribes to `task-events` (all event types). Writes structured JSON log per event. Minimal: just log to stdout (Loki-compatible). Add Helm deployment template.

### 2.3 Real-time Sync via WebSocket (Priority 3)
- **Why**: Spec lists Real-time Sync Service. Enables dashboard auto-refresh when chatbot modifies tasks.
- **How**: Add a `/ws/{user_id}` WebSocket endpoint to the backend. The existing `dispatchTaskUpdated` frontend event already handles UI refresh -- wire it to receive WS pushes instead of relying solely on polling. Alternatively, keep the current custom event approach and document it as the sync mechanism.

### 2.4 Dapr Cron Binding Wiring (Priority 4)
- **Why**: Spec section 5.2.3 says "Dapr cron binding runs every minute, triggering backend to check reminders." The cron YAML template exists but the backend endpoint needs the Dapr binding input route.
- **How**: Add `POST /reminder-cron` endpoint that Dapr invokes on schedule. It calls the existing `check_reminders()` logic. This completes the Dapr bindings building block.

### 2.5 Cloud Fallback YAML (AKS/GKE) (Priority 5)
- **Why**: Constitution 2.5 requires documented fallbacks. AKS/GKE YAML shows judges the fallback is real.
- **How**: Create `charts/todo-app/values-aks.yaml` and `values-gke.yaml` with provider-specific ingress class, image pull secrets, and node selectors. Brief comments explaining differences from OKE.

### 2.6 CI/CD Pipeline Verification (Priority 6)
- **Why**: FR-018 requires pipeline completing in < 15 minutes. The workflow exists but hasn't run.
- **How**: Trigger the GitHub Actions workflow manually. Capture screenshot of successful run (or fix any failures). Add screenshot to repo under `docs/cicd-proof.png`.

### 2.7 Phase V Unit Tests (Priority 7)
- **Why**: Constitution and spec require >80% test coverage per feature. No Phase V tests exist.
- **How**: Add `backend/tests/test_phase_v.py` with tests for: priority validation (P1-P4), tag sync (create + list), search query building, filter composition, recurrence depth check, reminder query. Mock the database session. Target: 10-15 tests covering critical paths.

### 2.8 Monitoring Helm Templates (Priority 8)
- **Why**: FR-019 requires pre-configured monitoring dashboards. Zero monitoring templates exist.
- **How**: Create `charts/todo-app/templates/monitoring/` with: `prometheus-rules.yaml` (4 alert rules from spec), `grafana-dashboard-configmap.yaml` (API metrics JSON). Conditional on `monitoring.enabled` value. Minimal but shows judges the pattern.

---

## 3. Implementation Guidelines

- **Reuse everything**: Notification/Audit consumers follow the exact same pattern as `recurring.py` (FastAPI + Dapr subscription). Copy and modify.
- **Dapr cron**: The `cron-binding.yaml` already exists. Just add the input binding route to the backend.
- **Fast Kafka choice**: Redpanda Cloud for cloud, Strimzi for local -- already configured.
- **Fast cloud choice**: Oracle OKE primary -- `values-cloud.yaml` already done. AKS/GKE YAMLs are thin overrides.
- **WebSocket**: Use FastAPI's built-in `WebSocket` support -- 30 lines of code max. Or document existing custom event mechanism as the real-time sync approach.
- **Tests**: Use `pytest` with `unittest.mock.patch` for DB session. No need for integration test infrastructure.
- **Monitoring**: Minimal ConfigMap with one Grafana dashboard JSON + one PrometheusRule YAML. Shows the pattern without heavy infra.
- **Timeline**: All 8 items completable in < 2 hours with focused execution.

---

## 4. Acceptance Criteria

1. `backend/consumers/notification.py` exists and handles `reminder.due` events with idempotent processing
2. `backend/consumers/audit.py` exists and logs all `task-events` to stdout in structured JSON
3. Backend has a `/reminder-cron` POST endpoint that Dapr cron binding invokes
4. `charts/todo-app/values-aks.yaml` and `values-gke.yaml` exist with valid YAML
5. `backend/tests/test_phase_v.py` has >= 10 tests covering priorities, tags, search, recurrence, reminders
6. `charts/todo-app/templates/monitoring/prometheus-rules.yaml` defines 4 alert rules
7. `charts/todo-app/templates/monitoring/grafana-dashboard-configmap.yaml` contains at least one dashboard
8. All consumers follow the same Dapr subscription pattern as `recurring.py`
9. `helm template` renders all new templates without errors
10. Frontend build continues to pass (`npx next build` exit code 0)

---

## 5. Risks & Quick Fixes

- **Notification consumer fails to connect to DB**: Reuse the same `DATABASE_URL` env var and session factory from backend. Copy `database/session.py` import pattern.
- **Dapr cron binding doesn't invoke endpoint**: Ensure the binding name matches (`reminder-cron`) and the route matches the binding's `route` metadata. Test with `curl -X POST localhost:8000/reminder-cron`.
- **Tests fail due to missing DB**: Use `unittest.mock.patch` to mock `session.exec()` and `session.get()`. No real DB needed for unit tests.
- **Monitoring YAML syntax errors**: Run `helm template` after creating each file. Fix immediately.
- **CI/CD workflow fails on first run**: Common causes: missing secrets in GitHub repo settings, incorrect Python version. Fix and re-run.
- **Time overrun**: Prioritize items 1-4 (consumers + cron binding) first -- these are the most impactful for judges. Items 5-8 are documentation/polish.
