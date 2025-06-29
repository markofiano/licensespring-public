# Ping Service with etcd Discovery

This repo contains:
- An etcd cluster deployed on AKS Kubernetes
- A Python Flask microservice "ping-service" that registers itself into etcd
- An aggregator client that queries etcd and calls all registered '/ping' endpoints

---

### Architecture overview

- **Ping Service**: Stateless Flask microservice that registers itself in etcd.
- **etcd Cluster**: StatefulSet of 3 replicas with client and peer communication.
- **Prometheus/Grafana**: Installed with Helm for metrics and visualization.

### Failover

- The etcd cluster is set up for HA. If one node fails, two others maintain quorum.
- The ping service is deployed as a Deployment with multiple replicas (2) for redundancy.

### Recovery

- Pods automatically restart on failure.
- etcd data persists using PVCs.
- To rejoin a failed etcd node, ensure it uses the same volume (PVC).

### Prerequisites if deployed on Azure

- Azure subscription
- AKS cluster
- Azure Container Registry (ACR)
- Helm installed locally
- kubectl access configured
- GitHub repository with secrets configured

## Repository Structure

```
ping-etcd-project/
├── charts/
│   └── etcd/                   
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── statefulset.yaml
│           └── service.yaml
│
├── ping-service/
│   ├── app.py                   
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── aggregator.py        
│   ├── values.yaml            
│   ├── templates/           
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── Chart.yaml
│
├── aggregator-pod.yaml       
└── README.md
```

---

##  Deployment Instructions

### 1. Deploy etcd Cluster via Helm
```bash
helm upgrade --install etcd ./charts/etcd --namespace default
```

### 2. Build & Push Docker Image
```bash
docker buildx build --platform linux/arm64 \
  -t <your-registry>/ping-service:latest \
  --push .
```

### 3. Deploy the Ping Service
```bash
helm upgrade --install ping ./ping-service \
  --namespace default \
  --set image.repository=<your-registry>/ping-service \
  --set image.tag=latest
```

### 4. Run Aggregator
```bash
kubectl apply -f aggregator-pod.yaml
kubectl logs pod/aggregator
```

---

## 5. Testing

### Check individual /ping
```bash
kubectl port-forward deployment/ping 5000:5000 &
curl http://localhost:5000/ping or open browser
Aggregator app: kubectl logs pod/aggregator
```

## 6. Monitoring with Prometheus and Grafana

1. Install using Helm:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus --namespace observability --create-namespace
```

2. Access Grafana:

```bash
kubectl get svc -n observability
```
Access via the external IP on port 80 (e.g., http://EXTERNAL-IP).

3. Access Prometheus:

```bash
kubectl port-forward svc/prometheus-server 9090:80 -n observability
```

### 7. Deploy Using GitHub Actions

Commit the repo to the GitHub repo, this pipeline uses Github Actions.
The etcd cluster is deployed manually by helm, and ping service is automatically updated as the part of CICD pipeline.
Modify the environment variables to your infrastructure, such as AKS cluster name and ACR name.

To enable the pipeline to deploy the application to Azure (AKS), you need to define the following secrets in GitHub repository:

| Secret Name              | 
|--------------------------|
| `AZURE_CREDENTIALS`      | 
| `AZURE_SUBSCRIPTION_ID`  |
| `ACR_USERNAME`           | 
| `ACR_PASSWORD`           | 
| `REGISTRY_LOGIN_SERVER`  | 
| `AKS_CLUSTER_NAME`       | 
| `AKS_RESOURCE_GROUP`     | 

### 8. Troubleshooting app

The issue could be potentialy related if the provided binary hi-devops is compiled for linux/amd64, then would fail when executed on an incompatible architecture such as arm64. This issue i previously encountered during deployment of the ping-service, where the Docker image was initially built for amd64 and failed on ARM based k8s nodes. Rebuilding the image for the correct architecture resolved issue.