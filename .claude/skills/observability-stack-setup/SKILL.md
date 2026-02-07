---
name: observability-stack-setup
description: Deploy Prometheus + Grafana for metrics, Loki for logging, and Jaeger for distributed tracing via Dapr. Configure alert rules for pod restarts, error rates, p95 latency, and Kafka consumer lag. Provision dashboards as code. Use when setting up monitoring for Phase V.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Observability Stack Setup

## Purpose

Deploy monitoring (Prometheus + Grafana), logging (Loki), and distributed tracing (Jaeger via Dapr) to the Kubernetes cluster. Provision dashboards as code and configure alerting rules for critical conditions.

## Used by

- Monitoring and Logging Agent (Agent 7)
- Cloud Deployment Agent (Agent 5) — resource awareness

## When to Use

- Installing kube-prometheus-stack via Helm
- Setting up Loki + Promtail for centralized logging
- Configuring Dapr distributed tracing with Jaeger/Zipkin
- Creating alert rules (pod restarts, error rates, latency, Kafka lag)
- Provisioning Grafana dashboards as ConfigMaps
- Verifying observability endpoints are healthy

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_target` | string | Yes | "minikube" or "cloud" |
| `services_to_monitor` | list | Yes | Services to observe |
| `alert_thresholds` | dict | No | Custom alert thresholds |
| `dashboard_definitions` | list | No | Grafana dashboard JSONs |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Helm values | YAML | kube-prometheus-stack config |
| Alert rules | YAML | PrometheusRule CRD |
| Dashboard ConfigMaps | YAML | Grafana dashboards as code |
| Dapr tracing config | YAML | Zipkin endpoint configuration |
| Access commands | bash | Port-forward for Grafana |

## Procedure

### Step 1: Install Monitoring Stack

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.resources.requests.memory=256Mi \
  --set grafana.resources.requests.memory=128Mi
```

### Step 2: Install Loki

```bash
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true
```

### Step 3: Configure Alert Rules

```yaml
- alert: PodRestartsTooHigh
  expr: increase(kube_pod_container_status_restarts_total{namespace="todo-app"}[5m]) > 3
- alert: HighErrorRate
  expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
- alert: HighP95Latency
  expr: histogram_quantile(0.95, ...) > 2
- alert: KafkaConsumerLagHigh
  expr: kafka_consumer_group_lag > 1000
```

### Step 4: Dapr Tracing

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: tracing-config
spec:
  tracing:
    samplingRate: "1"
    zipkin:
      endpointAddress: "http://monitoring-jaeger-collector.monitoring.svc:9411/api/v2/spans"
```

### Step 5: Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3001:80
```

## Quality Standards

- [ ] Resource limits on all monitoring components (fits Minikube/OKE free)
- [ ] Dashboards provisioned as ConfigMaps — not manually created
- [ ] Alert: pod restarts > 3 in 5min, errors > 5%, p95 > 2s, Kafka lag > 1000
- [ ] Loki retention: 72h Minikube, 7d cloud
- [ ] Dapr tracing: 100% dev, 10% production
- [ ] Port-forward commands provided for local Grafana access
- [ ] Prometheus scrapes Dapr sidecar metrics (port 9090)
