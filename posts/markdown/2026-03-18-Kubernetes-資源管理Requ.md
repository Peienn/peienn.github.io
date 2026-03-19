# Kubernetes 資源管理全攻略：從 Request/Limit 到 HPA 自動擴展的實戰指南

## 前言

在 Kubernetes 叢集中，資源管理是維持服務穩定性與成本效益的關鍵。你是否曾遇過 Pod 因為 OOMKilled 而不斷重啟？或是某個失控的服務吃光整個節點的 CPU，導致其他服務一起陣亡？這些問題的根源往往來自於資源配置不當。

本文將深入探討 Kubernetes 的資源管理機制，包括 Request 與 Limit 的正確設定方式，以及如何透過 HPA（Horizontal Pod Autoscaler）實現自動擴展，讓你的服務能夠優雅地應對流量波動。

## Request 與 Limit：資源配置的基石

Request 和 Limit 是 Kubernetes 資源管理的兩個核心概念。**Request** 代表 Pod 運行所需的最低保證資源，Scheduler 會依據 Request 來決定將 Pod 調度到哪個節點；**Limit** 則是 Pod 能使用的資源上限，超過此限制會觸發節流（CPU）或終止（Memory）。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: app
    image: nginx:1.25
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

在這個範例中，容器保證獲得 256Mi 記憶體和 0.25 核心 CPU，最多可使用 512Mi 記憶體和 0.5 核心 CPU。一個常見的經驗法則是將 Limit 設為 Request 的 1.5 到 2 倍，給予應用程式處理突發流量的彈性空間。

## QoS 類別：理解 Pod 的優先權

Kubernetes 根據 Request 和 Limit 的設定，自動將 Pod 分為三種 QoS（Quality of Service）類別，這決定了節點資源不足時的驅逐順序：

| QoS 類別 | 條件 | 驅逐優先權 |
|----------|------|------------|
| Guaranteed | Request = Limit（且皆有設定） | 最低 |
| Burstable | Request < Limit（或部分設定） | 中等 |
| BestEffort | 完全未設定 Request 和 Limit | 最高 |

檢查 Pod 的 QoS 類別：

```bash
kubectl get pod <pod-name> -o jsonpath='{.status.qosClass}'
```

對於關鍵服務，建議設定為 Guaranteed 類別，確保在資源競爭時不會被優先驅逐。對於非關鍵的批次任務，可以使用 BestEffort 來最大化資源利用率。

## LimitRange 與 ResourceQuota：叢集層級的防護網

單純依賴開發者自行設定 Request/Limit 並不可靠。透過 **LimitRange** 可以為 Namespace 設定預設值與範圍限制：

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "4Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
```

搭配 **ResourceQuota** 限制整個 Namespace 的資源總量：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
```

## HPA 自動擴展：讓服務彈性應對流量

當流量變化超出單一 Pod 的處理能力時，HPA 能根據指標自動調整副本數。首先確保叢集已安裝 Metrics Server：

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl top pods  # 驗證 Metrics Server 運作正常
```

建立基於 CPU 使用率的 HPA：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

這個配置設定當 CPU 使用率超過 70% 或記憶體超過 80% 時觸發擴展，並透過 `behavior` 設定縮容時的穩定視窗為 5 分鐘，避免流量波動造成頻繁的 Pod 數量震盪。

監控 HPA 狀態：

```bash
kubectl get hpa web-app-hpa --watch
```

## 結論與行動建議

有效的 Kubernetes 資源管理需要多層次的策略配合：

1. **立即執行**：檢視現有 Deployment，確保所有容器都設定了適當的 Request 和 Limit
2. **短期目標**：為各 Namespace 建立 LimitRange 和 ResourceQuota，建立資源防護機制
3. **中期優化**：部署 HPA 並根據實際負載模式調整擴展策略
4. **持續改進**：導入 Prometheus + Grafana 監控資源使用趨勢，定期使用 `kubectl top` 或 VPA（Vertical Pod Autoscaler）的建議值來優化配置

記住，資源管理不是一次性的設定，而是需要根據應用程式的實際行為持續調整的過程。從保守的設定開始，透過觀察與監控逐步優化，才能在穩定性與成本效益之間取得最佳平衡。

---
date: 2026-03-18
topic: Kubernetes 資源管理：Request、Limit 與 HPA 自動擴展
tags: [devops, kubernetes, k8s, resource-management, hpa, autoscaling, capacity-planning]
---