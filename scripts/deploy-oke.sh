#!/bin/bash
# Deploy Todo AI Chatbot to Oracle OKE
# Run this script in OCI Cloud Shell
set -e

NAMESPACE="todo-app"
REGISTRY="bom.ocir.io"
TENANCY_NS="bmmpta9gsjks"
REPO_URL="https://github.com/Shumailaaijaz/phase-5-advanced-cloud-deployment.git"
OCIR_USER="bmmpta9gsjks/shumailaaijaz359@gmail.com"
OCIR_TOKEN='H#wdH:Ke6yJ1Q_eKuDu:'

echo "=== Phase V: Deploying Todo AI Chatbot to OKE ==="

# Step 1: Create namespace (if not exists)
kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace $NAMESPACE already exists"

# Step 2: Create OCIR registry secret
echo "Creating OCIR registry secret..."
kubectl delete secret ocir-secret -n $NAMESPACE 2>/dev/null || true
kubectl create secret docker-registry ocir-secret \
  --docker-server=$REGISTRY \
  --docker-username="$OCIR_USER" \
  --docker-password="$OCIR_TOKEN" \
  --docker-email="shumailaaijaz359@gmail.com" \
  -n $NAMESPACE

# Step 3: Create Kaniko Docker config secret (for pushing)
echo "Creating Kaniko push credentials..."
DOCKER_CONFIG=$(echo -n "{\"auths\":{\"$REGISTRY\":{\"username\":\"$OCIR_USER\",\"password\":\"$OCIR_TOKEN\"}}}" | base64 -w0)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: kaniko-secret
  namespace: $NAMESPACE
type: Opaque
data:
  config.json: $DOCKER_CONFIG
EOF

# Step 4: Create OCIR repository (public)
echo "Creating OCIR repositories..."
oci artifacts container repository create \
  --compartment-id ocid1.tenancy.oc1..aaaaaaaafy5c5qe7rmkhldqtzwfnne6u3izqvljwg62yluru3onedhdwc5sa \
  --display-name todo-backend \
  --is-public true 2>/dev/null || echo "Backend repo may already exist"

oci artifacts container repository create \
  --compartment-id ocid1.tenancy.oc1..aaaaaaaafy5c5qe7rmkhldqtzwfnne6u3izqvljwg62yluru3onedhdwc5sa \
  --display-name todo-frontend \
  --is-public true 2>/dev/null || echo "Frontend repo may already exist"

# Step 5: Build backend image with Kaniko
echo "=== Building backend image with Kaniko ==="
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: kaniko-backend
  namespace: $NAMESPACE
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 300
  template:
    spec:
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        args:
        - "--context=git://$REPO_URL#refs/heads/main"
        - "--context-sub-path=backend"
        - "--dockerfile=Dockerfile"
        - "--destination=$REGISTRY/$TENANCY_NS/todo-backend:latest"
        - "--cache=false"
        - "--push-retry=3"
        volumeMounts:
        - name: kaniko-secret
          mountPath: /kaniko/.docker
      restartPolicy: Never
      volumes:
      - name: kaniko-secret
        secret:
          secretName: kaniko-secret
          items:
          - key: config.json
            path: config.json
EOF

# Step 6: Build frontend image with Kaniko
echo "=== Building frontend image with Kaniko ==="
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: kaniko-frontend
  namespace: $NAMESPACE
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 300
  template:
    spec:
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        args:
        - "--context=git://$REPO_URL#refs/heads/main"
        - "--context-sub-path=frontend"
        - "--dockerfile=Dockerfile"
        - "--destination=$REGISTRY/$TENANCY_NS/todo-frontend:latest"
        - "--build-arg=NEXT_PUBLIC_API_URL=http://todo-app-backend:8000"
        - "--cache=false"
        - "--push-retry=3"
        volumeMounts:
        - name: kaniko-secret
          mountPath: /kaniko/.docker
      restartPolicy: Never
      volumes:
      - name: kaniko-secret
        secret:
          secretName: kaniko-secret
          items:
          - key: config.json
            path: config.json
EOF

# Step 7: Wait for builds to complete
echo "Waiting for backend build..."
kubectl wait --for=condition=complete job/kaniko-backend -n $NAMESPACE --timeout=600s || {
  echo "Backend build failed! Checking logs..."
  kubectl logs job/kaniko-backend -n $NAMESPACE
  exit 1
}
echo "Backend image built successfully!"

echo "Waiting for frontend build..."
kubectl wait --for=condition=complete job/kaniko-frontend -n $NAMESPACE --timeout=600s || {
  echo "Frontend build failed! Checking logs..."
  kubectl logs job/kaniko-frontend -n $NAMESPACE
  exit 1
}
echo "Frontend image built successfully!"

echo ""
echo "=== Both images built and pushed to OCIR! ==="
echo "Backend:  $REGISTRY/$TENANCY_NS/todo-backend:latest"
echo "Frontend: $REGISTRY/$TENANCY_NS/todo-frontend:latest"
echo ""
echo "Now run deploy-oke-helm.sh to deploy the app!"
