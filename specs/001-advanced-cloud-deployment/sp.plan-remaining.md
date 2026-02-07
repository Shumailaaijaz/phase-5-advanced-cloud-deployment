# Phase V Plan – Remaining Tasks Only (Urgent Finish)

**Date**: February 08, 2026 – Crunch Time
**Owner**: Shumaila
**Status**: URGENT | **Estimated Total**: ~2.5 hours
**Spec**: [spec.md](./spec.md) | **Tasks**: [tasks.md](./tasks.md)

---

## 1. Goal Before Deadline

Complete the 9 critical missing pieces to reach ~95% Phase V compliance and maximize hackathon scoring across features, event-driven architecture, cloud deployment, CI/CD, and polish.

---

## 2. Prioritized Task List (do in this exact order)

### V5-R01 — Simple Reminders Consumer
- **Time**: 20 min | **Agent**: Event-Driven Architecture
- **What**: Create `backend/consumers/notification.py` — FastAPI app subscribing to `reminders` topic via Dapr. On `reminder.due` event: log the reminder (`print(f"REMINDER: {task_title} due at {due_date}")`), mark `reminder_sent=True` in DB. Track `event_id` for idempotency. Copy pattern from `recurring.py`.
- **Proof**: `notification.py` exists, logs reminder when cron triggers, `reminder_sent` flips to True.

### V5-R02 — Basic WebSocket Endpoint for Sync
- **Time**: 15 min | **Agent**: Feature Developer
- **What**: Add `WebSocket /ws/{user_id}` endpoint to `main.py`. On connect: store in `ws_connections` dict. On task event: broadcast JSON `{event_type, data}` to user's connections. Use FastAPI's built-in `WebSocket` — no extra dependencies. ~25 lines of code.
- **Proof**: Connect via browser DevTools, see task events arrive in real-time.

### V5-R03 — Audit Log Consumer
- **Time**: 15 min | **Agent**: Event-Driven Architecture
- **What**: Create `backend/consumers/audit.py` — subscribes to `task-events` topic. Logs every event as structured JSON to stdout (`json.dumps({audit: True, event_id, event_type, user_id, task_id, timestamp})`). Loki-compatible. Copy Dapr subscription pattern from `recurring.py`.
- **Proof**: `audit.py` exists, structured JSON lines appear in stdout when tasks are created/updated.

### V5-R04 — Dapr Cron Binding Wiring
- **Time**: 10 min | **Agent**: Dapr Integration
- **What**: If `cron-binding.yaml` exists but backend lacks the input route: add `POST /reminder-cron` endpoint to `main.py` that calls existing `check_reminders()` logic. Dapr invokes this every minute. If YAML missing: create `charts/todo-app/templates/dapr/cron-binding.yaml` with `bindings.cron`, schedule `@every 1m`, direction `input`.
- **Proof**: `curl -X POST localhost:8000/reminder-cron` returns `{checked: N, sent: M}`.

### V5-R05 — Cloud Fallback Configs (AKS/GKE)
- **Time**: 15 min | **Agent**: Cloud Deployment
- **What**: Create `charts/todo-app/values-aks.yaml` (Azure ingress class `azure/application-gateway`, ACR image registry, managed identity) and `charts/todo-app/values-gke.yaml` (GCE ingress class, GCR/Artifact Registry, Workload Identity). Thin overrides of `values-cloud.yaml` with provider-specific comments.
- **Proof**: Both files exist, `helm template -f values-aks.yaml` renders without errors.

### V5-R06 — Trigger GitHub Actions & Screenshot
- **Time**: 15 min | **Agent**: Manual fast
- **What**: Push latest code to trigger `deploy.yml`. If secrets missing: add `GITHUB_TOKEN` (auto-available). Watch Actions tab. Screenshot the green pipeline. Save as `docs/cicd-proof.png`. If lint/test fails: fix and re-push.
- **Proof**: Screenshot of green Actions run in `docs/` folder.

### V5-R07 — Add MIT LICENSE + GitHub Topics
- **Time**: 5 min | **Agent**: Manual fast
- **What**: Create `LICENSE` at repo root with MIT text, copyright 2026. Go to GitHub repo Settings → add topics: `hackathon`, `todo-app`, `fastapi`, `nextjs`, `kafka`, `dapr`, `kubernetes`. Add description: "AI-powered Todo Chatbot with event-driven architecture".
- **Proof**: LICENSE file committed. Topics visible on repo page.

### V5-R08 — Basic Tests + Coverage Note
- **Time**: 25 min | **Agent**: Feature Developer
- **What**: Create `backend/tests/test_phase_v.py` with 10-15 tests: priority validation (P1-P4), tag model fields, TaskCreate with tags/recurrence/reminders, recurrence date advancement (daily/weekly/monthly), event schema serialization, pagination offset calculation. Use `unittest.mock.patch` — no real DB needed.
- **Proof**: `pytest tests/test_phase_v.py -v` shows 10+ tests passing.

### V5-R09 — /demo/ Folder + README Update
- **Time**: 20 min | **Agent**: Manual fast
- **What**: Take 4-6 screenshots: login page, dashboard with priority tasks, chat interface, task creation with tags, reminder log output, Helm template output. Save in `demo/` folder. Update README: add screenshots section with `![Dashboard](demo/dashboard.png)`, add consumers table, add monitoring section, add cloud fallbacks table, add test instructions.
- **Proof**: `demo/` folder with images, README references them.

---

## 3. Quick Rules for Fast Completion

- **Copy-paste pattern**: Notification and Audit consumers follow the exact same pattern as `recurring.py` — change topic name, event handler, done
- **Reuse Helm/Dapr code**: All Dapr YAMLs use same conditional `{{ if .Values.dapr.enabled }}` pattern
- **Fake complex parts**: Reminders = `print()` to stdout instead of real email/push. WebSocket = in-memory dict, no Redis needed
- **Commit after each task**: Don't batch — push frequently so GitHub Actions triggers
- **Screenshots immediately**: Take screenshot right after each feature works, don't postpone

---

## 4. Final Checklist (copy to README)

- [ ] V5-R01: Reminders consumer logs reminder.due events
- [ ] V5-R02: WebSocket /ws/{user_id} connects and broadcasts
- [ ] V5-R03: Audit logger outputs structured JSON for all task-events
- [ ] V5-R04: POST /reminder-cron endpoint invokable by Dapr cron
- [ ] V5-R05: values-aks.yaml + values-gke.yaml exist and render
- [ ] V5-R06: GitHub Actions screenshot in docs/
- [ ] V5-R07: MIT LICENSE + GitHub topics set
- [ ] V5-R08: 10+ Phase V unit tests passing
- [ ] V5-R09: /demo/ folder with screenshots, README updated
- [ ] All code pushed to main
- [ ] Frontend build passes (`npx next build`)
- [ ] Backend starts clean (`uvicorn main:app`)
