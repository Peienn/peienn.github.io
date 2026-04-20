# 解決 Prometheus 高基數問題：Label 設計與 Recording Rules 優化實戰

## 前言

當你的 Prometheus 監控系統從幾十台機器擴展到數百台，或是微服務數量快速增長時，你可能會發現 Prometheus 記憶體使用量暴增、查詢變慢，甚至 Grafana Dashboard 經常 timeout。這通常指向一個常見但容易被忽視的問題：**高基數（High Cardinality）**。

高基數問題是 Prometheus 在生產環境中最常遇到的效能瓶頸之一。不當的 label 設計可能讓時間序列數量從數千條暴增到數百萬條，直接癱瘓你的監控系統。本文將分享如何識別高基數問題、優化 label 設計，以及善用 Recording Rules 來提升查詢效能。

## 什麼是高基數？為何它會拖垮 Prometheus

Prometheus 以時間序列（Time Series）為儲存單位，每一組獨特的 metric name 加上 label 組合就構成一條時間序列。當某個 label 的可能值（cardinality）過多時，時間序列數量會呈指數級增長。

舉例來說，以下這個看似無害的 metric：

```promql
http_requests_total{service="api", user_id="12345", request_id="abc-xyz-123"}
```

如果 `user_id` 有 10 萬個不同值，`request_id` 更是每個請求都不同，這條 metric 會產生天文數字般的時間序列。

你可以透過以下 PromQL 查詢目前的時間序列總數：

```promql
prometheus_tsdb_head_series
```

若要找出哪些 metric 貢獻最多時間序列，可以使用：

```promql
topk(10, count by (__name__) ({__name__=~".+"}))
```

當時間序列超過百萬條時，Prometheus 的記憶體消耗和查詢延遲都會顯著惡化。

## Label 設計的黃金守則

避免高基數的核心原則是：**Label 的值必須是有界且可枚舉的**。以下是幾個實務建議：

**應該使用的 label：**
- 環境：`env="production"`
- 服務名稱：`service="payment-api"`
- HTTP 狀態碼：`status_code="200"`
- 區域：`region="ap-northeast-1"`

**絕對要避免的 label：**
- 使用者 ID、Session ID
- Request ID、Trace ID
- 時間戳記
- 任何可能無限增長的識別符

如果你需要追蹤個別請求，應該使用專門的 tracing 工具（如 Jaeger、Tempo），而非塞進 Prometheus。

針對已經存在的高基數 metric，可以在 Prometheus 設定中使用 `metric_relabel_configs` 來移除問題 label：

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['localhost:8080']
    metric_relabel_configs:
      - source_labels: [user_id]
        action: labeldrop
      - source_labels: [__name__]
        regex: 'expensive_metric_.*'
        action: drop
```

## 善用 Recording Rules 預先聚合

即使 label 設計得當，在 Grafana 上查詢大範圍時間區間的聚合資料時，仍可能造成 Prometheus 高負載。Recording Rules 能預先計算並儲存聚合結果，大幅降低查詢成本。

在 Prometheus 設定中加入 Recording Rules：

```yaml
# /etc/prometheus/rules/recording_rules.yml
groups:
  - name: http_aggregations
    interval: 30s
    rules:
      - record: job:http_requests_total:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job, service)
      
      - record: job:http_request_duration_seconds:p99
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))
      
      - record: service:error_rate:ratio
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
          /
          sum(rate(http_requests_total[5m])) by (service)
```

Recording Rules 的命名慣例建議遵循 `level:metric:operations` 格式，例如 `job:http_requests_total:rate5m`，這能讓團隊成員快速理解這條 metric 的聚合層級。

## Grafana Dashboard 查詢優化

在 Grafana 端，也有幾個技巧可以減少對 Prometheus 的衝擊：

**1. 優先使用 Recording Rules 產生的 metric：**

```promql
# 避免：每次都即時計算
sum(rate(http_requests_total[5m])) by (service)

# 推薦：使用預先計算的結果
job:http_requests_total:rate5m
```

**2. 限制時間範圍與解析度：**

在 Dashboard 設定中設定合理的最小查詢間隔：

```json
{
  "interval": "30s",
  "maxDataPoints": 1000
}
```

**3. 使用變數時加上適當限制：**

```promql
# 避免載入所有 label 值
label_values(http_requests_total, service)

# 加上篩選條件
label_values(http_requests_total{env="$env"}, service)
```

## 結論與行動建議

高基數問題是 Prometheus 監控規模化的最大障礙，但只要掌握正確的設計原則，就能有效避免。以下是你可以立即採取的行動：

1. **立即檢查**：執行 `topk(10, count by (__name__) ({__name__=~".+"}))` 找出時間序列最多的 metric
2. **審視 Label**：確認所有 label 的 cardinality 都是有界的，移除任何 ID 類型的 label
3. **建立 Recording Rules**：為 Dashboard 常用的聚合查詢建立預先計算規則
4. **設定告警**：監控 `prometheus_tsdb_head_series` 並設定閾值告警

監控系統本身也需要被監控——定期檢視 Prometheus 的健康狀態，才能確保它在關鍵時刻不會掉鏈子。

---
date: 2026-04-20
topic: Prometheus & Grafana
tags: [devops, prometheus, grafana, monitoring, high-cardinality, performance-tuning]
---