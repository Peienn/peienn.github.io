# Capacity Planning 實戰指南：從流量預測到資源規劃的完整方法論

## 前言

凌晨三點，手機突然響起——線上服務因流量暴增而崩潰，團隊緊急擴容卻發現雲端帳號的配額早已用盡。這個場景對許多 DevOps 工程師來說並不陌生。Capacity Planning（容量規劃）正是為了避免這種窘境而存在的關鍵實踐。

良好的容量規劃不僅能確保系統在流量高峰時維持穩定，更能在成本與效能之間取得平衡。隨著雲端服務按需計費的模式普及，過度配置意味著浪費預算，配置不足則可能導致服務中斷。本文將介紹一套實用的容量規劃方法論，幫助你建立可預測、可擴展的基礎設施。

## 建立流量基準線：用數據說話

容量規劃的第一步是了解現況。透過監控工具收集歷史數據，建立流量基準線（Baseline），才能進行有意義的預測。

使用 Prometheus 搭配 PromQL 查詢過去 30 天的請求量趨勢：

```promql
# 計算每小時平均 QPS
rate(http_requests_total[1h])

# 找出過去 30 天的流量峰值
max_over_time(rate(http_requests_total[5m])[30d:1h])

# 計算 P95 回應時間趨勢
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

建議追蹤的核心指標包括：

- **QPS（Queries Per Second）**：每秒請求數
- **併發連線數**：同時在線的連線數量
- **資源使用率**：CPU、記憶體、磁碟 I/O、網路頻寬
- **回應時間分布**：P50、P95、P99 延遲

將這些數據匯入 Grafana 建立儀表板，設定每週自動產出報告，讓團隊對系統負載有清晰的認知。

## 流量預測模型：從歷史推估未來

有了基準線，下一步是建立預測模型。常見的預測方法包括線性回歸、時間序列分析與季節性調整。

以下是使用 Python 進行簡單流量預測的範例：

```python
import pandas as pd
from prophet import Prophet

# 載入歷史流量數據
df = pd.read_csv('traffic_data.csv')
df.columns = ['ds', 'y']  # Prophet 要求的欄位格式

# 建立預測模型
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=True
)
model.fit(df)

# 預測未來 90 天
future = model.make_future_dataframe(periods=90)
forecast = model.predict(future)

# 輸出預測峰值
peak_traffic = forecast['yhat_upper'].max()
print(f"預估 90 天內流量峰值: {peak_traffic:.0f} QPS")
```

除了演算法預測，也要納入業務因素考量：行銷活動、產品發布、季節性促銷等都會造成流量異常。建議與產品、行銷團隊建立定期同步機制，將已知事件納入預測模型。

## 資源需求計算：轉換流量為基礎設施規格

預測出流量後，需要將其轉換為具體的資源需求。這需要先進行壓力測試，了解單一節點的處理能力。

使用 k6 進行負載測試：

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // 漸增到 100 VUs
    { duration: '5m', target: 500 },   // 漸增到 500 VUs
    { duration: '2m', target: 1000 },  // 壓力測試峰值
    { duration: '1m', target: 0 },     // 降載
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% 請求需在 200ms 內完成
    http_req_failed: ['rate<0.01'],    // 錯誤率低於 1%
  },
};

export default function () {
  const res = http.get('https://api.example.com/endpoint');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

執行測試並記錄結果：

```bash
k6 run --out json=results.json load-test.js
```

根據測試結果，計算所需節點數量：

```
所需節點數 = (預測峰值 QPS × 安全係數) ÷ 單節點最大 QPS

範例：(5000 × 1.5) ÷ 800 = 9.375 → 至少需要 10 個節點
```

安全係數通常設定在 1.3 到 1.5 之間，為突發流量預留緩衝空間。

## 自動化擴縮容策略：讓系統自我調節

靜態配置難以應對瞬息萬變的流量。透過 Kubernetes HPA（Horizontal Pod Autoscaler）實現自動擴縮容：

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 5
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "500"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

同時設定 Cluster Autoscaler 確保節點層級也能自動調整：

```bash
# 檢查 Cluster Autoscaler 狀態
kubectl -n kube-system logs -l app=cluster-autoscaler --tail=50
```

## 結論與行動建議

Capacity Planning 不是一次性的任務，而是持續迭代的過程。以下是立即可執行的行動清單：

1. **本週**：部署監控儀表板，開始收集流量基準線數據
2.