# Quickstart: Phase V — Advanced Cloud Deployment

**Date**: 2026-02-07 | **Plan**: [plan.md](./plan.md)

---

## Prerequisites

- Docker Desktop with WSL2 (existing from Phase IV)
- Minikube v1.38.0+ (existing from Phase IV)
- Helm v3.x (existing from Phase IV)
- Dapr CLI v1.13+ (`curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash`)
- Python 3.11+ with `pip` (existing from Phase III)
- Node.js 18+ with `npm` (existing from Phase III)

## Quick Start — Local Development (No K8s)

```bash
# 1. Install new Python dependencies
cd backend
pip install aiokafka httpx croniter

# 2. Run Alembic migrations
alembic upgrade head

# 3. Start backend with Dapr disabled (direct mode)
USE_DAPR=false python -m uvicorn main:app --reload

# 4. Start frontend
cd ../frontend && npm run dev
```

## Quick Start — Minikube with Dapr + Kafka

```bash
# 1. Run the deploy script (handles everything)
bash scripts/deploy-local.sh

# 2. Access the app
minikube service todo-frontend -n todo-app

# 3. Teardown when done
bash scripts/teardown-local.sh
```

## Quick Start — Cloud (Oracle OKE)

```bash
# 1. Configure kubectl for OKE
export KUBECONFIG=~/.kube/oke-config

# 2. Install Dapr on cluster
dapr init -k --runtime-version 1.13.0

# 3. Deploy with cloud values
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-cloud.yaml \
  --atomic --timeout 10m --wait

# 4. Verify
kubectl get pods -n todo-app
curl -I https://todo.example.com
```

## Migration Order

Run in sequence — each depends on the previous:

```bash
# These are Alembic migrations, not manual SQL
alembic upgrade 004  # Priority enum (P1-P4)
alembic upgrade 005  # Tags (tag + task_tag tables)
alembic upgrade 006  # Search vector (TSVECTOR + GIN index)
alembic upgrade 007  # Due date type (VARCHAR → TIMESTAMPTZ)
alembic upgrade 008  # Recurrence (rule, parent_id, depth)
alembic upgrade 009  # Reminders (minutes, sent flag)

# Or all at once:
alembic upgrade head
```

## Key Environment Variables

| Variable | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `DATABASE_URL` | Yes | — | Neon PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | Yes | — | JWT signing secret |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `USE_DAPR` | No | `true` | Toggle Dapr vs direct Kafka |
| `KAFKA_BROKERS` | If USE_DAPR=false | — | Kafka bootstrap servers |
| `KAFKA_USERNAME` | If cloud Kafka | — | SASL username |
| `KAFKA_PASSWORD` | If cloud Kafka | — | SASL password |
