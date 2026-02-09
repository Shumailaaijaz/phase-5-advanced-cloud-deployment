#!/bin/bash
# Deploy Todo App with Helm to OKE
# Run AFTER deploy-oke.sh completes (images built)
set -e

NAMESPACE="todo-app"
REGISTRY="bom.ocir.io"
TENANCY_NS="bmmpta9gsjks"

echo "=== Deploying Todo App with Helm ==="

# Clone repo (if not already)
if [ ! -d "phase-5-advanced-cloud-deployment" ]; then
  echo "Cloning repository..."
  git clone https://github.com/Shumailaaijaz/phase-5-advanced-cloud-deployment.git
fi
cd phase-5-advanced-cloud-deployment

# Prompt for secrets
if [ -z "$DATABASE_URL" ]; then
  echo "Enter DATABASE_URL (Neon PostgreSQL):"
  read -r DATABASE_URL
fi
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Enter OPENAI_API_KEY:"
  read -r OPENAI_API_KEY
fi
if [ -z "$BETTER_AUTH_SECRET" ]; then
  echo "Enter BETTER_AUTH_SECRET:"
  read -r BETTER_AUTH_SECRET
fi

# Deploy with Helm
echo "Running helm upgrade --install..."
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-cloud.yaml \
  --set frontend.image.repository=$REGISTRY/$TENANCY_NS/todo-frontend \
  --set frontend.image.tag=latest \
  --set backend.image.repository=$REGISTRY/$TENANCY_NS/todo-backend \
  --set backend.image.tag=latest \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  --set backend.secrets.openaiApiKey="$OPENAI_API_KEY" \
  --set backend.secrets.betterAuthSecret="$BETTER_AUTH_SECRET" \
  --set backend.secrets.jwtSecret="$BETTER_AUTH_SECRET" \
  --set dapr.enabled=false \
  --set consumers.recurring.enabled=false \
  --set consumers.notification.enabled=false \
  --set consumers.audit.enabled=false \
  --set monitoring.enabled=false \
  --set ingress.enabled=false \
  --set frontend.service.type=LoadBalancer \
  --set backend.service.type=LoadBalancer \
  --set "global.imagePullSecrets[0].name=ocir-secret" \
  --namespace $NAMESPACE \
  --create-namespace \
  --timeout 10m \
  --wait

echo ""
echo "=== Deployment Complete! ==="
echo ""
kubectl get pods -n $NAMESPACE
echo ""
kubectl get svc -n $NAMESPACE
echo ""
echo "Waiting for LoadBalancer IP..."
sleep 30
kubectl get svc -n $NAMESPACE
echo ""
echo "Access your app at the EXTERNAL-IP shown above!"
