# Oracle Cloud OKE Cluster + VS Code Deployment Guide (Error-Free)

**Date**: February 2026 | **Author**: Shumaila
**Target**: Always Free tier | VM.Standard.A1.Flex | 4 OCPUs, 24 GB RAM
**Platform**: Windows 10/11 + WSL2 Ubuntu + VS Code

---

## Prerequisites (check these first)

Before starting, verify ALL of these. Missing any one = blocked later.

```bash
# 1. OCI CLI installed and configured
oci --version
# Expected: Oracle Cloud Infrastructure CLI 3.x.x
# If missing: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm

# 2. OCI CLI config exists
cat ~/.oci/config
# Must show: [DEFAULT] section with user, fingerprint, tenancy, region, key_file

# 3. kubectl installed
kubectl version --client
# Expected: Client Version: v1.28+ or higher
# If missing:
# curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
# chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# 4. VS Code accessible from WSL2
code --version
# Expected: 1.9x.x or higher
# If "command not found": Open VS Code on Windows, press Ctrl+Shift+P → "Shell Command: Install 'code' command in PATH"

# 5. WSL2 has internet access
curl -s https://cloud.oracle.com | head -1
# Should return HTML. If not, check DNS: echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# 6. OCI tenancy has Always Free eligible resources
oci iam region list --output table
# Check your home region — this is where Always Free resources MUST be created

# 7. Python 3 available (needed for some OCI CLI plugins)
python3 --version

# 8. Helm installed (for later Todo app deployment)
helm version
# If missing:
# curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### IMPORTANT for Pakistan Users

```
REGION SELECTION:
- Best regions for Pakistan: ap-mumbai-1 (Mumbai) or ap-hyderabad-1 (Hyderabad)
- These give lowest latency (50-80ms vs 200ms+ for US/EU regions)
- Your HOME REGION is set during signup and CANNOT be changed
- Always Free resources can ONLY be created in your home region
- If you signed up with US region: you're stuck with it (still works, just slower)

FREE TIER LIMITS (as of 2026):
- 4 OCPUs total (Ampere A1) — can split across multiple VMs
- 24 GB RAM total
- 200 GB block volume
- OKE control plane is FREE (managed by Oracle)
- Worker nodes use YOUR free compute — so 1 node with 4 OCPUs, 24GB
- Load Balancer: 1 free (10 Mbps flexible shape)
- NEVER create more than these limits or you WILL be charged
```

---

## Step 1: Create OKE Cluster (Always Free)

### Option A: OCI Console (Recommended for first time)

```
1. Go to: https://cloud.oracle.com → Sign in
2. Hamburger menu (☰) → Developer Services → Kubernetes Clusters (OKE)
3. Click "Create Cluster"
4. Choose "Quick Create" (NOT Custom Create — Quick Create sets up VCN, subnets, etc.)
5. Configure:
   - Name: todo-cluster
   - Compartment: (your root compartment)
   - Kubernetes Version: v1.30.x (latest stable)
   - Kubernetes API Endpoint: Public Endpoint ← IMPORTANT for VS Code access
   - Node Type: Managed
   - Shape: VM.Standard.A1.Flex (Ampere — this is the Always Free one)
   - OCPUs: 4
   - Memory: 24 GB
   - Number of nodes: 1 ← IMPORTANT: only 1 node to stay in free tier
   - Image: Oracle Linux 8 (default)
6. Click "Next" → Review → Click "Create Cluster"
7. WAIT 10-15 minutes for cluster to be ACTIVE
```

### Option B: OCI CLI (faster if you know your compartment OCID)

```bash
# Get your compartment OCID (root compartment)
COMPARTMENT_ID=$(oci iam compartment list --all --query "data[?\"name\"=='<your-tenancy-name>'].id | [0]" --raw-output 2>/dev/null)

# If above doesn't work, get it from console:
# Identity → Compartments → Copy OCID of root compartment
# Or use tenancy OCID directly:
COMPARTMENT_ID=$(oci iam tenancy get --query "data.id" --raw-output)

echo "Compartment: $COMPARTMENT_ID"

# Create VCN first (OKE needs networking)
VCN_ID=$(oci network vcn create \
  --compartment-id "$COMPARTMENT_ID" \
  --display-name "todo-vcn" \
  --cidr-blocks '["10.0.0.0/16"]' \
  --query "data.id" --raw-output)

echo "VCN: $VCN_ID"

# Create Internet Gateway
IGW_ID=$(oci network internet-gateway create \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --display-name "todo-igw" \
  --is-enabled true \
  --query "data.id" --raw-output)

# Create Route Table with internet access
RT_ID=$(oci network route-table create \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --display-name "todo-rt" \
  --route-rules "[{\"destination\":\"0.0.0.0/0\",\"networkEntityId\":\"$IGW_ID\",\"destinationType\":\"CIDR_BLOCK\"}]" \
  --query "data.id" --raw-output)

# Create Security List (allow all for simplicity — tighten later)
SL_ID=$(oci network security-list list \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --query "data[0].id" --raw-output)

# Create Subnet for OKE nodes
SUBNET_ID=$(oci network subnet create \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --display-name "todo-node-subnet" \
  --cidr-block "10.0.1.0/24" \
  --route-table-id "$RT_ID" \
  --security-list-ids "[\"$SL_ID\"]" \
  --query "data.id" --raw-output)

# Create API endpoint subnet
API_SUBNET_ID=$(oci network subnet create \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --display-name "todo-api-subnet" \
  --cidr-block "10.0.0.0/28" \
  --route-table-id "$RT_ID" \
  --security-list-ids "[\"$SL_ID\"]" \
  --query "data.id" --raw-output)

# Create Service LB subnet
LB_SUBNET_ID=$(oci network subnet create \
  --compartment-id "$COMPARTMENT_ID" \
  --vcn-id "$VCN_ID" \
  --display-name "todo-lb-subnet" \
  --cidr-block "10.0.2.0/24" \
  --route-table-id "$RT_ID" \
  --security-list-ids "[\"$SL_ID\"]" \
  --query "data.id" --raw-output)

echo "Subnets created. Creating OKE cluster..."

# Create OKE cluster
CLUSTER_ID=$(oci ce cluster create \
  --compartment-id "$COMPARTMENT_ID" \
  --name "todo-cluster" \
  --kubernetes-version "v1.30.1" \
  --vcn-id "$VCN_ID" \
  --endpoint-subnet-id "$API_SUBNET_ID" \
  --service-lb-subnet-ids "[\"$LB_SUBNET_ID\"]" \
  --endpoint-public-ip-enabled true \
  --query "data.id" --raw-output)

echo "Cluster ID: $CLUSTER_ID"
echo "Waiting for cluster to become ACTIVE (10-15 min)..."

# Wait for cluster
oci ce cluster get --cluster-id "$CLUSTER_ID" --query "data.\"lifecycle-state\"" --raw-output
# Repeat until it shows "ACTIVE"

# Create Node Pool (Always Free shape)
# Get the availability domain first
AD=$(oci iam availability-domain list --compartment-id "$COMPARTMENT_ID" --query "data[0].name" --raw-output)

# Get latest Oracle Linux 8 image for A1
IMAGE_ID=$(oci compute image list \
  --compartment-id "$COMPARTMENT_ID" \
  --shape "VM.Standard.A1.Flex" \
  --operating-system "Oracle Linux" \
  --operating-system-version "8" \
  --sort-by TIMECREATED --sort-order DESC \
  --query "data[0].id" --raw-output)

oci ce node-pool create \
  --compartment-id "$COMPARTMENT_ID" \
  --cluster-id "$CLUSTER_ID" \
  --name "todo-pool" \
  --kubernetes-version "v1.30.1" \
  --node-shape "VM.Standard.A1.Flex" \
  --node-shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
  --node-image-id "$IMAGE_ID" \
  --size 1 \
  --placement-configs "[{\"availabilityDomain\":\"$AD\",\"subnetId\":\"$SUBNET_ID\"}]"

echo "Node pool creating... Wait another 5-10 min for node to be Ready"
```

### Verify Cluster is Active

```bash
# Check cluster state (repeat until ACTIVE)
oci ce cluster get --cluster-id "$CLUSTER_ID" \
  --query "data.{Name: name, State: \"lifecycle-state\", K8s: \"kubernetes-version\"}" \
  --output table

# Check node pool (repeat until node shows ACTIVE)
oci ce node-pool list --compartment-id "$COMPARTMENT_ID" \
  --cluster-id "$CLUSTER_ID" \
  --query "data[].{Name: name, Nodes: \"node-config-details\".size, State: \"lifecycle-state\"}" \
  --output table
```

---

## Step 2: Download & Configure kubeconfig

```bash
# Create .kube directory if it doesn't exist
mkdir -p ~/.kube

# Download kubeconfig from OKE
# Replace CLUSTER_ID with your actual cluster OCID
oci ce cluster create-kubeconfig \
  --cluster-id "$CLUSTER_ID" \
  --file ~/.kube/config \
  --region ap-mumbai-1 \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT

# Verify kubeconfig was created
cat ~/.kube/config | head -5
# Should show: apiVersion: v1, clusters:, etc.

# Set correct permissions (kubectl complains if too open)
chmod 600 ~/.kube/config

# TEST CONNECTION — this is the moment of truth
kubectl get nodes
# Expected output (after node is ready):
# NAME         STATUS   ROLES   AGE   VERSION
# 10.0.1.xxx   Ready    node    5m    v1.30.1

# If you see "Ready" — you're golden!
# If you see "NotReady" — wait 2-3 more minutes, node is still initializing
```

### Fix: "Unable to connect to the server: dial tcp... connection refused"

```bash
# This means the API endpoint is not reachable. Common causes:

# 1. Cluster API is private (not public)
# Fix: Recreate with public endpoint, or set up OCI Bastion

# 2. WSL2 DNS issue
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
# Then retry kubectl get nodes

# 3. Corporate firewall/VPN blocking port 6443
# Fix: Disconnect VPN, or add OKE API IP to allowlist

# 4. Kubeconfig has wrong endpoint
kubectl config view --minify | grep server
# Should show: https://<public-ip>:6443
# If it shows a private IP (10.x.x.x), you need public endpoint
```

### Fix: "error: exec plugin is configured to use API version client.authentication.k8s.io/v1beta1"

```bash
# This means your kubectl is too old for the OCI auth plugin
# Update kubectl:
curl -LO "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/kubectl

# Also ensure OCI CLI is in PATH for the exec auth plugin
which oci
# Must return a path. If not:
export PATH=$PATH:~/bin  # or wherever oci is installed
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
```

---

## Step 3: Set up VS Code + Kubernetes Extension

### Install Extensions

```
In VS Code (Ctrl+Shift+X → search and install):

1. "Kubernetes" by Microsoft (ID: ms-kubernetes-tools.vscode-kubernetes-tools)
2. "YAML" by Red Hat (ID: redhat.vscode-yaml) — for manifest editing
3. "Remote - WSL" by Microsoft (ID: ms-vscode-remote.remote-wsl) — if not already
```

### Configure Kubernetes Extension for WSL2

```bash
# The Kubernetes extension needs to find kubeconfig in WSL2.
# If you opened VS Code from WSL (code .), it should auto-detect.

# Verify VS Code is running in WSL mode:
# Bottom-left corner should show "WSL: Ubuntu" (green icon)

# If Kubernetes sidebar shows "No clusters found":

# Option 1: Set KUBECONFIG explicitly in VS Code settings
# Ctrl+Shift+P → "Preferences: Open Settings (JSON)" → add:
# "vs-kubernetes": {
#   "vs-kubernetes.kubeconfig": "/home/<your-user>/.kube/config"
# }

# Option 2: Symlink (if VS Code runs on Windows side)
# In PowerShell (Windows):
# mkdir $env:USERPROFILE\.kube -Force
# wsl cat ~/.kube/config > $env:USERPROFILE\.kube\config
```

### Verify Cluster Appears in VS Code

```
1. Click the Kubernetes icon in the left sidebar (looks like a ship wheel)
2. You should see "todo-cluster" under "Clusters"
3. Expand it → Namespaces → default
4. If you see the node under "Nodes" → you're connected!

If NOT visible:
- Ctrl+Shift+P → "Kubernetes: Set Kubeconfig" → select ~/.kube/config
- Or click the refresh icon at the top of the Kubernetes sidebar
```

---

## Step 4: Deploy a Simple Container from VS Code

### Create a Test Deployment

```bash
# Create a working directory
mkdir -p ~/k8s-test && cd ~/k8s-test
```

Create file `test-deploy.yaml` in VS Code:

```yaml
# test-deploy.yaml — Simple nginx deployment to verify OKE works
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-nginx
  namespace: default
  labels:
    app: test-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-nginx
  template:
    metadata:
      labels:
        app: test-nginx
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: test-nginx-svc
  namespace: default
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 80
  selector:
    app: test-nginx
```

### Deploy from VS Code (2 ways)

```
Method 1: Right-click in VS Code
1. Open test-deploy.yaml in editor
2. Right-click anywhere in the file
3. Click "Kubernetes: Apply" (or "Apply to Cluster")
4. Select the context (todo-cluster)
5. See "Applied" confirmation in the terminal

Method 2: VS Code terminal (Ctrl+`)
```

```bash
kubectl apply -f test-deploy.yaml
# Expected:
# deployment.apps/test-nginx created
# service/test-nginx-svc created
```

### Verify Pod is Running

```bash
# Check pods
kubectl get pods -w
# Wait until STATUS shows "Running" (may take 1-2 min for image pull)
# NAME                          READY   STATUS    RESTARTS   AGE
# test-nginx-xxxxx-yyyyy        1/1     Running   0          45s

# Check in VS Code:
# Kubernetes sidebar → Workloads → Deployments → test-nginx
# Right-click pod → "Describe" to see full status
# Right-click pod → "Logs" to see nginx access logs
# Right-click pod → "Terminal" to exec into the container

# Port-forward to test locally
kubectl port-forward svc/test-nginx-svc 8080:80
# Open browser: http://localhost:8080 → Should show "Welcome to nginx!"
# Ctrl+C to stop port-forward

# Clean up test deployment
kubectl delete -f test-deploy.yaml
```

---

## Step 5: Troubleshooting Checklist

### Error 1: "connection refused" or "i/o timeout"

```bash
# Cause: OKE API endpoint not reachable
# Fix 1: Check cluster has PUBLIC endpoint
oci ce cluster get --cluster-id "$CLUSTER_ID" \
  --query "data.\"endpoint-config\".\"is-public-ip-access-enabled\"" --raw-output
# Must show: true

# Fix 2: WSL2 DNS broken
sudo sh -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'

# Fix 3: VPN/proxy interference
# Disconnect VPN and retry
```

### Error 2: "Unauthorized" or "forbidden"

```bash
# Cause: OCI token expired or wrong user
# Fix: Regenerate kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id "$CLUSTER_ID" \
  --file ~/.kube/config \
  --region ap-mumbai-1 \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT \
  --overwrite

# Verify OCI CLI auth works
oci iam user get --user-id $(oci iam user list --query "data[0].id" --raw-output) --query "data.name" --raw-output
```

### Error 3: "No nodes available" / node NotReady

```bash
# Cause: Node pool still provisioning or shape unavailable
# Fix 1: Wait 5-10 more minutes
kubectl get nodes -w

# Fix 2: Check node pool status
oci ce node-pool list --compartment-id "$COMPARTMENT_ID" \
  --cluster-id "$CLUSTER_ID" --query "data[].{Name:name, State:\"lifecycle-state\"}" --output table

# Fix 3: A1 shape capacity issue (common in popular regions)
# Oracle sometimes runs out of A1 capacity
# Error: "Out of host capacity"
# Fix: Try again in 30 min, or try a different availability domain
# For Mumbai: AD-1 is usually more available than AD-2/AD-3
```

### Error 4: "OCI CLI not found" in kubectl auth

```bash
# Cause: OKE kubeconfig uses OCI CLI for authentication
# The exec plugin can't find oci binary
which oci  # Must return a path

# Fix: Add OCI CLI to PATH in .bashrc
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
source ~/.bashrc

# Also set in VS Code terminal profile:
# Ctrl+Shift+P → "Terminal: Select Default Profile" → bash
```

### Error 5: "ImagePullBackOff" on pod

```bash
# Cause: Can't pull container image (private registry, rate limit)
kubectl describe pod <pod-name> | grep -A5 "Events"

# Fix 1: Docker Hub rate limit — use specific tag, not :latest
# Fix 2: For GHCR private images, create image pull secret:
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USER \
  --docker-password=YOUR_GITHUB_PAT \
  --docker-email=your@email.com

# Add to deployment:
# spec.template.spec.imagePullSecrets:
#   - name: ghcr-secret
```

### Error 6: "Insufficient CPU/memory" on scheduling

```bash
# Cause: Requesting more resources than your free-tier node has
# Free tier: 4 OCPUs, 24 GB total — but system pods use ~1 OCPU, 4 GB

# Fix: Keep your deployments small
# Good: requests cpu 100m, memory 128Mi
# Bad: requests cpu 2000m, memory 8Gi (leaves no room for other pods)

kubectl describe node | grep -A5 "Allocated resources"
# Shows how much is used vs available
```

### Error 7: VS Code Kubernetes sidebar empty

```bash
# Fix 1: Reload window
# Ctrl+Shift+P → "Developer: Reload Window"

# Fix 2: Set kubeconfig path explicitly
# Ctrl+Shift+P → "Kubernetes: Set Kubeconfig" → browse to ~/.kube/config

# Fix 3: Check VS Code is in WSL mode (bottom-left = "WSL: Ubuntu")
# If not: Ctrl+Shift+P → "Remote-WSL: Reopen in WSL"
```

### Error 8: "error: exec plugin is configured to use API version v1beta1"

```bash
# Fix: Update kubectl to latest
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/kubectl
```

### Error 9: "Out of host capacity" when creating node pool

```bash
# This is an Oracle Cloud capacity issue — very common for A1 shape
# The free A1 instances are popular and regions run out

# Fix 1: Retry every 15-30 minutes (capacity frees up)
# Fix 2: Try a different Availability Domain in same region
# Fix 3: Try a different region (if you have access)
# Fix 4: Use a smaller shape (2 OCPUs, 12 GB) — still free
# Fix 5: Script that auto-retries:
while true; do
  oci ce node-pool create \
    --compartment-id "$COMPARTMENT_ID" \
    --cluster-id "$CLUSTER_ID" \
    --name "todo-pool" \
    --kubernetes-version "v1.30.1" \
    --node-shape "VM.Standard.A1.Flex" \
    --node-shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
    --node-image-id "$IMAGE_ID" \
    --size 1 \
    --placement-configs "[{\"availabilityDomain\":\"$AD\",\"subnetId\":\"$SUBNET_ID\"}]" \
    && break
  echo "Capacity not available, retrying in 60s..."
  sleep 60
done
```

### Error 10: Load Balancer stuck in "Creating" state

```bash
# Free tier gives 1 load balancer (10 Mbps flexible)
# If you already have one, creating another will fail

# Check existing LBs:
oci lb load-balancer list --compartment-id "$COMPARTMENT_ID" \
  --query "data[].{Name:\"display-name\", State:\"lifecycle-state\", Shape:\"shape-name\"}" \
  --output table

# Fix: Delete unused LBs, or use NodePort/ClusterIP instead of LoadBalancer type
```

---

## Step 6: Deploy Your Todo App (quick notes)

```bash
# Assuming your Helm chart is at charts/todo-app/

# 1. Set your secrets
export DATABASE_URL="postgresql://user:pass@host/dbname?sslmode=require"
export OPENAI_API_KEY="sk-..."
export BETTER_AUTH_SECRET="your-jwt-secret"
export JWT_SECRET="your-jwt-secret"

# 2. Create namespace
kubectl create namespace todo-app

# 3. Deploy with Helm using cloud values
helm upgrade --install todo-app charts/todo-app \
  -f charts/todo-app/values-cloud.yaml \
  --set backend.secrets.databaseUrl="$DATABASE_URL" \
  --set backend.secrets.openaiApiKey="$OPENAI_API_KEY" \
  --set backend.secrets.betterAuthSecret="$BETTER_AUTH_SECRET" \
  --set backend.secrets.jwtSecret="$JWT_SECRET" \
  --namespace todo-app \
  --create-namespace \
  --atomic \
  --timeout 10m

# 4. Verify all pods running
kubectl get pods -n todo-app -w
# Wait until all show Running with 1/1 (or 2/2 if Dapr enabled)

# 5. Check services
kubectl get svc -n todo-app

# 6. Port-forward to test locally (if no ingress)
kubectl port-forward svc/todo-app-backend 8000:8000 -n todo-app &
kubectl port-forward svc/todo-app-frontend 3000:3000 -n todo-app &

# Open: http://localhost:3000

# 7. View in VS Code
# Kubernetes sidebar → Namespaces → todo-app → expand to see all resources
# Right-click any pod → Logs, Describe, Terminal

# 8. Rollback if something breaks
helm rollback todo-app 1 -n todo-app --wait
```

### Cost Safety Check

```bash
# ALWAYS verify you're within free tier limits:
# - 1 node with VM.Standard.A1.Flex (4 OCPUs, 24GB)
# - 1 Load Balancer (10 Mbps flexible shape)
# - 200 GB boot volume
# - No extra block volumes

# Check compute usage:
oci compute instance list --compartment-id "$COMPARTMENT_ID" \
  --query "data[].{Name:\"display-name\", Shape:shape, State:\"lifecycle-state\"}" \
  --output table

# Check block volumes:
oci bv volume list --compartment-id "$COMPARTMENT_ID" \
  --query "data[].{Name:\"display-name\", Size:\"size-in-gbs\", State:\"lifecycle-state\"}" \
  --output table

# If you see anything beyond free tier limits → delete immediately
# Oracle charges are real money — monitor billing daily during hackathon
```

---

## Quick Reference Card

```
OKE Cluster Status:    oci ce cluster get --cluster-id $CLUSTER_ID --query "data.\"lifecycle-state\""
Get kubeconfig:        oci ce cluster create-kubeconfig --cluster-id $CLUSTER_ID --file ~/.kube/config --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT
Check nodes:           kubectl get nodes
Check all pods:        kubectl get pods --all-namespaces
Deploy manifest:       kubectl apply -f <file.yaml>
Helm install:          helm upgrade --install <name> <chart> -f <values> --namespace <ns> --atomic
Helm rollback:         helm rollback <name> <revision> --namespace <ns>
Port forward:          kubectl port-forward svc/<name> <local>:<remote> -n <ns>
View logs:             kubectl logs -f <pod-name> -n <ns>
Exec into pod:         kubectl exec -it <pod-name> -n <ns> -- /bin/sh
Delete everything:     helm uninstall todo-app -n todo-app && kubectl delete ns todo-app
```
