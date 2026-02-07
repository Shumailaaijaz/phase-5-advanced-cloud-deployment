#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# teardown-local.sh — Clean up all local Minikube resources
# Usage: bash scripts/teardown-local.sh
# =============================================================================

echo "========================================="
echo "Phase V: Local Teardown — teardown-local.sh"
echo "========================================="

echo ">>> Uninstalling Helm release..."
helm uninstall todo-app --namespace todo-app 2>/dev/null || echo "  No Helm release found."

echo ">>> Deleting namespaces..."
kubectl delete namespace todo-app --ignore-not-found
kubectl delete namespace kafka --ignore-not-found

echo ">>> Removing Dapr from cluster..."
dapr uninstall -k 2>/dev/null || echo "  Dapr not installed."

echo ">>> Stopping Minikube..."
minikube stop

echo ""
echo "========================================="
echo "Teardown complete!"
echo "========================================="
