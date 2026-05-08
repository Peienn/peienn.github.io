# 解決 Istio mTLS 配置不一致導致的服務間通訊失敗問題

## 前言

當你在 Kubernetes 叢集中導入 Istio Service Mesh 後，最常遇到的困擾之一就是「服務突然無法互相溝通」。明明昨天還正常運作，今天某個 Pod 重啟後就開始噴出 `503 Service Unavailable` 或 `connection reset by peer` 的錯誤。

追查後發現，問題根源往往出在 mTLS（mutual TLS）配置不一致——部分服務強制使用加密連線，部分服務卻還在 plaintext 模式。這種「半導入」狀態在逐步遷移至 Service Mesh 的過程中極為常見，卻也最容易被忽略。

本文將深入分析 mTLS 配置不一致的成因，並提供具體的診斷與修復方法。

## 理解 Istio mTLS 的三種模式

Istio 的 PeerAuthentication 資源控制著服務接收請求時的 mTLS 行為，共有三種模式：

| 模式 | 行為描述 |
|------|----------|
| DISABLE | 只接受 plaintext 連線 |
| PERMISSIVE | 同時接受 plaintext 與 mTLS 連線 |
| STRICT | 只接受 mTLS 連線 |

預設情況下，Istio 採用 `PERMISSIVE` 模式，這是為了讓遷移過程更平滑。但當你在 namespace 層級設定了 `STRICT`，卻有個別服務尚未注入 sidecar，災難就發生了。

```yaml
# 這個設定會讓整個 namespace 強制 mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
```

## 快速診斷 mTLS 狀態

當服務通訊異常時，第一步是確認雙方的 mTLS 狀態是否匹配。使用 `istioctl` 提供的診斷工具：

```bash
# 檢查特定服務的 mTLS 狀態
istioctl x describe pod <pod-name> -n <namespace>

# 輸出範例：
# Pod: order-service-7d4f8b9c6-x2k9m
# Pod Ports: 8080 (order-service), 15090 (istio-proxy)
# Suggestion: mTLS is STRICT for this workload. Ensure clients have sidecars.
```

另一個實用指令是直接檢視 Envoy 的配置，確認 listener 是否正確綁定 TLS：

```bash
# 進入 sidecar 檢查 listener 配置
istioctl proxy-config listeners <pod-name> -n <namespace> -o json | \
  jq '.[] | select(.name | contains("inbound")) | .filterChains[].transportSocket'
```

如果輸出中沒有 `tls_context`，代表該 inbound listener 仍在接收 plaintext。

## 常見問題場景與修復方案

### 場景一：新部署的服務沒有 sidecar

確認 namespace 已啟用自動注入：

```bash
kubectl get namespace production --show-labels | grep istio-injection
```

若缺少 label，執行：

```bash
kubectl label namespace production istio-injection=enabled
kubectl rollout restart deployment -n production
```

### 場景二：部分 workload 需要排除 mTLS

某些服務（如連接外部資料庫的 client）可能需要特殊處理。可針對特定 workload 設定例外：

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: db-client-exception
  namespace: production
spec:
  selector:
    matchLabels:
      app: db-client
  mtls:
    mode: PERMISSIVE
```

### 場景三：DestinationRule 與 PeerAuthentication 衝突

這是最隱蔽的問題。即使服務端設定了 `STRICT`，若 client 端的 DestinationRule 指定 `DISABLE`，連線依然會失敗：

```yaml
# 錯誤配置：強制 client 發送 plaintext
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service
  namespace: production
spec:
  host: payment-service
  trafficPolicy:
    tls:
      mode: DISABLE  # 這會覆蓋自動 mTLS
```

修復方式是改為 `ISTIO_MUTUAL`，讓 Istio 自動處理憑證：

```yaml
trafficPolicy:
  tls:
    mode: ISTIO_MUTUAL
```

## 建立可觀測性防護網

長期來看，僅靠人工檢查不夠可靠。建議在 Prometheus 中監控 mTLS 相關指標：

```promql
# 監控 mTLS 連線失敗率
sum(rate(istio_requests_total{
  connection_security_policy!="mutual_tls",
  reporter="destination"
}[5m])) by (destination_service)
```

搭配 Grafana 設定告警，當非 mTLS 流量超過閾值時即時通知，避免問題擴散。

## 結論與行動建議

mTLS 配置不一致是 Istio 導入過程中最常見的絆腳石，但只要掌握正確的診斷工具與設定邏輯，就能快速定位問題。

建議的行動步驟：
1. **盤點現況**：用 `istioctl analyze` 掃描整個叢集的配置衝突
2. **統一策略**：在 mesh 層級設定 `PERMISSIVE`，逐個 namespace 升級為 `STRICT`
3. **建立監控**：將 mTLS 狀態納入 SLO 指標，異常時自動告警
4. **文件化例外**：所有 `DISABLE` 或 `PERMISSIVE` 例外都應有明確註解與 owner

Service Mesh 的價值在於統一管理，但前提是配置的一致性。花時間建立標準流程，能省下無數深夜除錯的痛苦。

---
date: 2026-05-08
topic: Service Mesh
tags: [devops, istio, mtls, kubernetes, service-mesh, security, troubleshooting]
---