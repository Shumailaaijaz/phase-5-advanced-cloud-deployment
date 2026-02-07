#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# deploy-local.sh — Full Minikube + Dapr + Kafka deployment
# Usage: bash scripts/deploy-local.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Phase V: Local Deployment — deploy-local.sh"
echo "========================================="

# ── Step 1: Ensure Minikube is running ──────────────────────────────────────
echo ""
echo ">>> Step 1/7: Checking Minikube..."
if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube with 6GB RAM and 3 CPUs..."
    minikube start --memory=6144 --cpus=3 --driver=docker
else
    echo "Minikube already running."
fi

# ── Step 2: Install Dapr on cluster ─────────────────────────────────────────
echo ""
echo ">>> Step 2/7: Installing Dapr on Kubernetes..."
if ! kubectl get namespace dapr-system &>/dev/null; then
    dapr init -k --runtime-version 1.13.0
    echo "Waiting for Dapr system pods..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/part-of=dapr -n dapr-system --timeout=120s
else
    echo "Dapr already installed."
fi

# ── Step 3: Install Strimzi Kafka operator ──────────────────────────────────
echo ""
echo ">>> Step 3/7: Installing Strimzi Kafka operator..."
if ! kubectl get namespace kafka &>/dev/null; then
    kubectl create namespace kafka
    kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka
    echo "Waiting for Strimzi operator pod..."
    kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator -n kafka --timeout=180s
else
    echo "Strimzi already installed."
fi

# ── Step 4: Deploy ephemeral Kafka cluster ──────────────────────────────────
echo ""
echo ">>> Step 4/7: Deploying Kafka cluster..."
if ! kubectl get kafka kafka-cluster -n kafka &>/dev/null; then
    cat <<'KAFKAEOF' | kubectl apply -n kafka -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka-cluster
spec:
  kafka:
    version: 3.7.0
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
    storage:
      type: ephemeral
  zookeeper:
    replicas: 1
    storage:
      type: ephemeral
KAFKAEOF

    echo "Waiting for Kafka cluster to be ready (this may take 2-3 minutes)..."
    kubectl wait kafka/kafka-cluster --for=condition=Ready -n kafka --timeout=300s
else
    echo "Kafka cluster already running."
fi

# Create Kafka topics
echo "Creating Kafka topics..."
for TOPIC in task-events reminders task-updates; do
    if ! kubectl get kafkatopic "$TOPIC" -n kafka &>/dev/null; then
        cat <<TOPICEOF | kubectl apply -n kafka -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: $TOPIC
  labels:
    strimzi.io/cluster: kafka-cluster
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: $([ "$TOPIC" = "task-events" ] && echo "604800000" || echo "86400000")
TOPICEOF
        echo "  Created topic: $TOPIC"
    else
        echo "  Topic $TOPIC already exists."
    fi
done

# ── Step 5: Build Docker images in Minikube context ────────────────────────
echo ""
echo ">>> Step 5/7: Building Docker images..."
eval $(minikube docker-env)
docker build -t todo-backend:local "$PROJECT_ROOT/backend"
docker build -t todo-frontend:local "$PROJECT_ROOT/frontend"

# ── Step 6: Helm install ───────────────────────────────────────────────────
echo ""
echo ">>> Step 6/7: Deploying with Helm..."
kubectl create namespace todo-app --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install todo-app "$PROJECT_ROOT/charts/todo-app" \
    -f "$PROJECT_ROOT/charts/todo-app/values-local.yaml" \
    --namespace todo-app \
    --atomic \
    --timeout 10m \
    --wait

# ── Step 7: Verify ─────────────────────────────────────────────────────────
echo ""
echo ">>> Step 7/7: Verifying deployment..."
echo ""
kubectl get pods -n todo-app
echo ""
kubectl get pods -n kafka
echo ""
kubectl get pods -n dapr-system

echo ""
echo "========================================="
echo "Deployment complete!"
echo "Run: minikube service todo-frontend -n todo-app"
echo "========================================="
