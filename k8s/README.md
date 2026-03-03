# Kubernetes Deployment

**License:** MIT  
**Contact:** hasbullita007@gmail.com  
**Maintained by:** hasbulla

---

These manifests provide a starting point for running the Telegram Anti‑Fraud System on a
Kubernetes cluster (EKS/GKE/AKS or on‑prem).

All workloads are designed to be *stateless* except Redis and PostgreSQL. You will need
to build and publish the application image (e.g. `ghcr.io/<your-org>/telegram_antifraud:latest`)
and update the `image:` fields below accordingly.

## Components

1. **webhook** – receives Telegram webhooks, enqueues payloads to Redis stream.
2. **worker** – pulls from Redis and processes messages; horizontally scalable.
3. **redis** – StatefulSet with 3 replicas for cluster mode (requires persistent volumes).
4. **postgres** – Deployment with PVC for persistence; use managed service for production.
5. **services** – ClusterIP for internal communication.
6. **Ingress** – route `POST /webhook` with TLS to webhook service; use cert-manager.
7. **HPA** – horizontal pod autoscaler on CPU and queue length metric (via Prometheus).

## Applying manifests

```sh
kubectl apply -f k8s/redis-statefulset.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/webhook-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

Adjust resource requests/limits and image tags as appropriate.

---

Hecho por hasbulla
