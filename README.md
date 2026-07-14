# 🚀 OpenSRE Automated Kubernetes RCA using Prometheus, Alertmanager & Slack

## 📖 Project Overview

This project demonstrates an **AI-powered Root Cause Analysis (RCA)** workflow for Kubernetes incidents.

Instead of simply sending alerts to Slack, the system automatically:

1. Detects Kubernetes issues
2. Generates Prometheus alerts
3. Sends alerts to Alertmanager
4. Forwards alerts to a custom Flask Relay
5. Invokes OpenSRE AI Investigation
6. Generates an RCA
7. Sends the RCA to Slack

---

# Architecture

```
                    Kubernetes Cluster
                           │
                           │
                    kube-state-metrics
                           │
                           ▼
                     Prometheus
                (Evaluates Alert Rules)
                           │
                           ▼
                    Alertmanager
                    (Webhook POST)
                           │
                           ▼
               relay.py (Flask Webhook)
                           │
                           ▼
                 opensre investigate
                           │
                           ▼
                      OpenAI LLM
                           │
                           ▼
                    Root Cause Analysis
                           │
                           ▼
                         Slack
```

---

# Folder Structure

```
opensre-demo/
│
├── relay.py
├── alertmanager-values.yaml
├── prometheus-rules.yaml
├── bad-deployment.yaml
└── opensre/
      ├── .env
      └── OpenSRE source code
```

---

# Components

## 1. Kubernetes

Responsible for running workloads.

Example:

```
broken-app
```

If the image is wrong:

```
nginx:this-tag-does-not-exist
```

Pod becomes

```
ImagePullBackOff
```

---

## 2. kube-state-metrics

Collects Kubernetes object state.

Examples

```
Deployment replicas

Pod status

Namespace

Container state

Node status
```

Exports metrics like

```
kube_pod_container_status_waiting_reason

kube_deployment_status_replicas_available
```

---

## 3. Prometheus

Prometheus continuously scrapes metrics from kube-state-metrics.

Example:

```
kube_pod_container_status_waiting_reason
```

Every evaluation interval it checks alert rules.

---

## 4. Prometheus Rules

File

```
prometheus-rules.yaml
```

Contains rules like

```
PodImagePullBackOff

DeploymentReplicasZero

PodCrashLoopBackOff
```

Example

```
expr:

kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} == 1
```

If true for

```
30 seconds
```

Prometheus changes the alert to

```
FIRING
```

---

## 5. Alertmanager

Alertmanager receives alerts from Prometheus.

Configured in

```
alertmanager-values.yaml
```

Example

```yaml
receivers:
  - name: opensre-relay

    webhook_configs:
      - url: http://10.0.2.15:9600/alert
```

Alertmanager groups alerts and sends HTTP POST requests to relay.py.

---

## 6. relay.py

relay.py is a Flask application.

Runs on

```
Port 9600
```

Route

```
POST /alert
```

Responsibilities

- Receive webhook from Alertmanager
- Parse JSON
- Ignore resolved alerts
- Filter allowed alerts
- Convert alert into OpenSRE input format
- Save alert into temporary JSON
- Execute OpenSRE investigation
- Print logs

---

## 7. Flask

Flask is a lightweight Python web server.

Instead of writing an HTTP server from scratch, Flask provides

```
@app.route("/alert")
```

to receive requests.

Alertmanager sends

```
HTTP POST
```

to

```
http://VM-IP:9600/alert
```

Flask receives it.

---

## 8. Temporary Alert JSON

relay.py creates

```
/tmp/tmpxxxxx.json
```

Example

```json
{
  "alertname":"PodImagePullBackOff",
  "namespace":"default",
  "pod":"broken-app",
  "severity":"critical"
}
```

This file becomes the input for OpenSRE.

---

## 9. OpenSRE

Command executed

```
uv run \
--project ~/opensre-demo/opensre \
opensre investigate \
-i /tmp/tmpxxxxx.json
```

OpenSRE

Reads alert

↓

Collects evidence

↓

Calls LLM

↓

Generates RCA

↓

Sends Slack notification

---

## 10. Slack

Slack receives

- Alert Summary

- Root Cause

- Findings

- Recommendations

---

# Important Files

## relay.py

Receives alerts

Calls OpenSRE

---

## prometheus-rules.yaml

Defines

```
PodImagePullBackOff

DeploymentReplicasZero

CrashLoopBackOff
```

---

## alertmanager-values.yaml

Contains Alertmanager routing configuration.

Responsible for forwarding alerts to relay.py.

---

## bad-deployment.yaml

Creates a broken deployment

```
Image:
nginx:this-tag-does-not-exist
```

Used for demo purposes.

---

## .env

Stores

```
LLM Provider

Model

Authentication Method
```

Example

```
LLM_PROVIDER=openai

OPENAI_MODEL=gpt-5.4
```

---

# Complete Flow

```
Broken Deployment

↓

ImagePullBackOff

↓

kube-state-metrics exports metrics

↓

Prometheus scrapes metrics

↓

Prometheus Rule matches

↓

Alert becomes FIRING

↓

Alertmanager receives alert

↓

Webhook POST

↓

relay.py

↓

Create JSON

↓

opensre investigate

↓

OpenAI

↓

Root Cause

↓

Slack Notification
```

---

# Quick Setup Commands

## Start K3s

```bash
sudo systemctl start k3s
```

---

## Check Nodes

```bash
kubectl get nodes
```

---

## Check Pods

```bash
kubectl get pods -A
```

---

## Start Relay

```bash
sudo systemctl restart opensre-relay
```

---

## Relay Logs

```bash
sudo journalctl -fu opensre-relay
```

---

## OpenSRE Health Check

```bash
cd ~/opensre-demo/opensre

uv run opensre doctor
```

---

## Apply Prometheus Rules

```bash
kubectl apply -f prometheus-rules.yaml
```

---

## Update Alertmanager

```bash
helm upgrade kps prometheus-community/kube-prometheus-stack \
-n monitoring \
-f alertmanager-values.yaml
```

---

## Verify Alert Rules

```bash
kubectl get prometheusrule -n monitoring
```

---

## Check Running Alerts

```bash
curl -G http://localhost:9090/api/v1/query \
--data-urlencode 'query=ALERTS'
```

---

## Check ImagePullBackOff Metric

```bash
curl -G http://localhost:9090/api/v1/query \
--data-urlencode 'query=kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}'
```

---

## Check Alertmanager Alerts

```bash
curl http://localhost:9093/api/v2/alerts
```

---

## Create Broken Deployment

```bash
kubectl apply -f bad-deployment.yaml
```

---

## Fix Deployment

```bash
kubectl set image deployment/broken-app \
broken-app=nginx:latest
```

---

## Delete Demo

```bash
kubectl delete -f bad-deployment.yaml
```

---

# Troubleshooting

## No Slack Notification

Check relay

```
sudo journalctl -fu opensre-relay
```

---

Check OpenSRE

```
uv run opensre doctor
```

---

Check Alertmanager

```
curl http://localhost:9093/api/v2/alerts
```

---

Check Prometheus

```
curl http://localhost:9090/api/v1/alerts
```

---

Check kube-state-metrics

```
kubectl get pods -n monitoring
```

---

# Technologies Used

- Kubernetes
- K3s
- Prometheus
- kube-state-metrics
- Alertmanager
- Flask
- Python
- OpenSRE
- OpenAI GPT
- Slack
- systemd
- Helm

---

# Learning Outcomes

- Kubernetes Monitoring
- Prometheus Alert Rules
- Alertmanager Webhooks
- Flask Webhooks
- OpenSRE Investigations
- AI-based RCA
- Slack Automation
- Kubernetes Troubleshooting
- Production Monitoring Workflow
