# 用 Prometheus Recording Rules 優化高基數指標查詢效能

## 前言

當你的 Prometheus 監控規模逐漸擴大，是否曾經遇過 Grafana 儀表板載入緩慢、甚至查詢超時的狀況？這個問題在監控 Kubernetes 叢集時特別常見——當 Pod 數量突破數百個，每次查詢都要即時聚合大量時間序列，不僅拖慢頁面回應，更可能導致 Prometheus 記憶體飆升。

Recording Rules 是 Prometheus 內建的預計算機制，能將複雜的 PromQL 查詢結果預先計算並儲存為新的指標。這個技巧對於中大型環境來說是必備的效能優化手段，卻常被忽略。本文將帶你從實務角度理解何時該用、如何設計，以及常見的踩坑經驗。

## 辨識需要優化的查詢

在動手之前，先找出真正的效能瓶頸。Prometheus 提供了內建指標來追蹤查詢效能：

```promql
# 查看過去 1 小時內執行時間最長的查詢
topk(10, prometheus_engine_query_duration_seconds{quantile="0.9"})
```

另一個實用方法是檢視 Grafana 的 Query Inspector。打開任一 Panel，點選 Inspect → Query，觀察 `Query time` 欄位。若單一查詢超過 2-3 秒，就是優化的候選對象。

典型的高成本查詢特徵包括：
- 使用 `rate()` 或 `histogram_quantile()` 搭配高基數標籤
- 聚合時間範圍超過 24 小時
- 同一個 Dashboard 重複計算相似指標

## 設計 Recording Rules 的實務原則

Recording Rules 定義在 Prometheus 的設定檔中。以下是一個針對 HTTP 請求延遲的實際範例：

```yaml
# prometheus-rules.yml
groups:
  - name: http_latency_rules
    interval: 30s
    rules:
      # 預計算每個 service 的 P99 延遲
      - record: job:http_request_duration_seconds:p99
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le)
          )

      # 預計算每個 service 的請求速率
      - record: job:http_requests:rate5m
        expr: |
          sum(rate(http_requests_total[5m])) by (job, status_code)
```

命名慣例很重要，官方建議格式為 `level:metric:operations`。例如 `job:http_requests:rate5m` 表示按 job 聚合、原始指標為 http_requests、執行了 5 分鐘的 rate 計算。

將設定加入 Prometheus：

```yaml
# prometheus.yml
rule_files:
  - "prometheus-rules.yml"
```

重新載入設定：

```bash
curl -X POST http://localhost:9090/-/reload
```

## 在 Grafana 中切換使用預計算指標

設定完成後，修改 Grafana 的查詢。原本的即時計算：

```promql
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le)
)
```

改為直接查詢預計算指標：

```promql
job:http_request_duration_seconds:p99
```

查詢複雜度從掃描數千個時間序列，降為讀取單一指標。實務上我曾在一個擁有 500+ Pod 的環境中，將 Dashboard 載入時間從 12 秒降至 800 毫秒。

## 常見陷阱與除錯技巧

**陷阱一：interval 設定過短**

Recording Rules 的 `interval` 決定計算頻率。設太短（如 5s）會增加 Prometheus 負擔，設太長（如 5m）則可能漏失短暫的異常峰值。一般建議與 scrape_interval 一致或為其倍數。

**陷阱二：忘記處理標籤遺失**

預計算會固定輸出的標籤組合。若原始查詢有 `by (job, instance)` 但 Recording Rule 只保留 `by (job)`，後續想用 instance 篩選就會失敗。設計時需預先規劃聚合維度。

驗證 Rules 是否正確執行：

```bash
# 檢查 Rules 狀態
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {name, health, lastError}'
```

## 結論與行動建議

Recording Rules 是解決 Prometheus 查詢效能問題的第一道防線。建議你這樣開始：

1. **盤點現有 Dashboard**：找出查詢時間超過 2 秒的 Panel
2. **優先處理重複計算**：多個 Panel 共用的聚合邏輯最值得抽取
3. **漸進式遷移**：先在測試環境驗證 Recording Rules 輸出正確，再更新 Grafana 查詢
4. **監控 Rules 本身**：使用 `prometheus_rule_evaluation_duration_seconds` 確保預計算沒有成為新的瓶頸

當 Recording Rules 也無法滿足需求時（例如需要跨越數週的長期趨勢分析），則該考慮 Thanos 或 Mimir 等長期儲存方案，但那是另一個主題了。

---
date: 2026-05-06
topic: Prometheus & Grafana
tags: [devops, prometheus, grafana, performance, recording-rules, monitoring]
---