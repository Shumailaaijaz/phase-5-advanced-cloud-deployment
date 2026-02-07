---
name: ai-kubernetes-operations
description: Generate safe kubectl-ai and kagent commands for local Minikube Kubernetes operations. Use when deploying, scaling, debugging, or analyzing Kubernetes resources with AI-assisted tooling. Also use when diagnosing pod failures (CrashLoopBackOff, OOMKilled, ImagePullBackOff), optimizing resource allocations, writing kubectl-ai natural-language prompts, or interpreting kagent root-cause analysis output.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# AI Kubernetes Operations

## Purpose

Provide a procedural reference for generating safe, effective kubectl-ai and kagent commands targeting a local Minikube cluster. Every operation produces four outputs: the kubectl-ai command, expected YAML, plain kubectl equivalent, and verification steps.

## Used by

- ai-devops-k8s agent
- helm-chart-creator agent
- minikube-docker-setup agent (for post-setup verification)

## Procedure

### Step 1: Classify the Action

Determine the operation category before generating commands:

| Category | Examples | Safety Level |
|----------|----------|-------------|
| **Deploy** | Create deployment, service, ingress | Safe — generates new resources |
| **Scale** | Adjust replicas, HPA | Safe — modifies existing counts |
| **Update** | Change image, env vars, limits | Moderate — always dry-run first |
| **Debug** | Logs, describe, events, top | Read-only — always safe |
| **Analyze** | kagent diagnose, root-cause | Read-only — always safe |
| **Delete** | Remove specific resource | Destructive — require name + namespace confirmation |

### Step 2: Generate kubectl-ai Command

Write a natural-language prompt for kubectl-ai. Follow these prompt-engineering rules:

**Good prompts are specific:**
```bash
kubectl-ai 'create a deployment named todo-backend with image todo-backend:latest, \
  1 replica, port 8000, memory request 128Mi limit 512Mi, cpu request 100m limit 500m, \
  env DATABASE_URL from secret todo-secrets key database-url, \
  readiness probe httpGet /health port 8000 initialDelay 5s period 10s'
```

**Bad prompts are vague:**
```bash
# DON'T: kubectl-ai 'deploy my backend'
# DON'T: kubectl-ai 'fix the pod'
```

**Prompt checklist:**
- [ ] Resource type and name specified
- [ ] Image repository and tag included
- [ ] Ports explicitly stated
- [ ] Resource requests AND limits included
- [ ] Environment variables listed (with secret refs where needed)
- [ ] Probes defined (path, port, timing)
- [ ] Minikube constraints acknowledged (NodePort, single node, local images)

### Step 3: Show Expected YAML

Present the YAML that kubectl-ai should generate. Annotate non-obvious fields:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-backend
  namespace: todo-app           # Always namespace-scoped
  labels:
    app: todo-backend
spec:
  replicas: 1                   # Minikube: keep at 1-2
  selector:
    matchLabels:
      app: todo-backend
  template:
    metadata:
      labels:
        app: todo-backend
    spec:
      containers:
        - name: todo-backend
          image: todo-backend:latest
          imagePullPolicy: IfNotPresent  # Local images: Never or IfNotPresent
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: 100m         # Minikube safe floor
              memory: 128Mi
            limits:
              cpu: 500m         # ~2x request
              memory: 512Mi     # ~4x request
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          envFrom:
            - secretRef:
                name: todo-secrets
            - configMapRef:
                name: todo-config
```

### Step 4: Provide Plain kubectl Equivalent

Always include the non-AI alternative:

```bash
# Option A: Apply from file
kubectl apply -f todo-backend-deployment.yaml -n todo-app

# Option B: Imperative create (simple cases)
kubectl create deployment todo-backend \
  --image=todo-backend:latest \
  --replicas=1 \
  -n todo-app \
  --dry-run=client -o yaml > todo-backend-deployment.yaml
# Then edit the YAML to add probes, resources, env, and apply
```

### Step 5: Verification Commands

Provide verification appropriate to the action category:

**After Deploy/Update:**
```bash
kubectl get pods -n todo-app -w                    # Watch pod status
kubectl describe pod -l app=todo-backend -n todo-app  # Check events
kubectl logs -l app=todo-backend -n todo-app --tail=50  # Check startup logs
```

**After Scale:**
```bash
kubectl get pods -n todo-app                       # Confirm replica count
kubectl top pods -n todo-app                       # Check resource distribution
```

**After Delete:**
```bash
kubectl get all -n todo-app                        # Confirm resource removed
```

## Debugging Playbooks

### CrashLoopBackOff

```bash
# 1. Gather diagnostics
kubectl logs <pod> -n todo-app --previous          # Last crash output
kubectl describe pod <pod> -n todo-app             # Events section
kubectl get pod <pod> -n todo-app -o jsonpath='{.status.containerStatuses[0].lastState}'

# 2. AI diagnosis
kubectl-ai 'show me why pod <pod> in namespace todo-app is crash looping'

# 3. kagent root-cause
kagent analyze pod <pod> -n todo-app

# 4. Common fixes
# Missing env var → check secret/configmap exists:
kubectl get secret todo-secrets -n todo-app -o yaml
# Wrong entrypoint → check image CMD:
kubectl run debug --image=todo-backend:latest -n todo-app --command -- sleep 3600
kubectl exec -it debug -n todo-app -- sh
```

### OOMKilled

```bash
# 1. Check current limits vs actual usage
kubectl describe pod <pod> -n todo-app | grep -A5 'Limits'
kubectl top pod <pod> -n todo-app

# 2. AI fix
kubectl-ai 'increase memory limit for deployment todo-backend in todo-app to 512Mi, keep request at 128Mi'

# 3. Verify after fix
kubectl get pod <pod> -n todo-app -w
kubectl top pod <pod> -n todo-app
```

### ImagePullBackOff

```bash
# 1. Check image name
kubectl describe pod <pod> -n todo-app | grep 'Image:'
kubectl describe pod <pod> -n todo-app | grep -A5 'Events'

# 2. For local Minikube images — load into Minikube's Docker daemon
eval $(minikube docker-env)
docker build -t todo-backend:latest ./backend
# OR
minikube image load todo-backend:latest

# 3. Ensure imagePullPolicy is IfNotPresent or Never for local images
kubectl-ai 'patch deployment todo-backend in todo-app to set imagePullPolicy to IfNotPresent'
```

### Pending Pods

```bash
# 1. Check node capacity
kubectl describe node minikube | grep -A10 'Allocated resources'
kubectl top node

# 2. Check PVC bindings (if pod uses volumes)
kubectl get pvc -n todo-app

# 3. If resources insufficient
# Restart minikube with more resources:
minikube stop
minikube start --memory=4096 --cpus=2 --driver=docker
```

## kagent Analysis Commands

Use kagent for complex, multi-resource diagnosis:

```bash
# Analyze a specific pod
kagent analyze pod <pod-name> -n todo-app

# Diagnose an entire namespace
kagent diagnose namespace todo-app

# Root-cause analysis for a failing deployment
kagent analyze deployment todo-backend -n todo-app

# Interpret output: kagent returns structured findings
# - Severity: Critical / Warning / Info
# - Root cause: the detected issue
# - Recommendation: suggested fix command
# Always cross-verify kagent recommendations with kubectl describe before applying
```

## Minikube Resource Budget

Reference limits for the Todo Chatbot stack on a 4 GB WSL2 allocation:

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|------------|-----------|----------------|-------------|
| frontend | 100m | 500m | 128Mi | 512Mi |
| backend | 100m | 500m | 128Mi | 512Mi |
| mcp-server | 100m | 500m | 128Mi | 512Mi |
| **Total** | **300m** | **1500m** | **384Mi** | **1536Mi** |

Leaves ~2.5 GB for Kubernetes system components and OS overhead.

## Safety Guardrails

Commands that are **NEVER** generated:

| Forbidden Command | Reason |
|-------------------|--------|
| `kubectl delete --all` | Cluster-wide destruction |
| `kubectl delete namespace kube-system` | Kills cluster control plane |
| `kubectl drain minikube` | Single-node cluster — draining kills everything |
| Removing resource limits entirely | Risks OOM on constrained Minikube |
| `kubectl edit` on system resources | Unstable cluster state |

Commands that **ALWAYS** require dry-run first:

```bash
# Before any apply/patch/replace, generate and review:
kubectl-ai '<prompt>' --dry-run=client -o yaml > review.yaml
cat review.yaml   # Human reviews
kubectl apply -f review.yaml -n todo-app
```

## Output Format

For every operation, deliver:

1. **kubectl-ai command** — copy-pasteable, with well-crafted natural-language prompt
2. **Expected YAML** — annotated with inline comments on key fields
3. **Plain kubectl equivalent** — for environments without kubectl-ai
4. **Verification steps** — confirm success, check logs, watch pod status
