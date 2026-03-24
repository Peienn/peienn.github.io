# 用 Prometheus 建立有效的 Capacity Planning 預警機制：避免半夜被叫醒的實戰指南

## 前言

你是否有過這樣的經驗：半夜三點收到告警，發現某台服務器的磁碟空間已經 100% 滿了，或是記憶體 OOM 導致服務崩潰？這些問題其實都可以透過良好的 Capacity Planning 預警機制提前發現並處理。

Capacity Planning 不只是預測未來需要多少資源，更重要的是建立一套能夠「提前告訴你問題即將發生」的監控系統。本文將聚焦在如何使用 Prometheus 建立實用的容量預警規則，讓你從被動救火轉為主動預防。

## 為什麼傳統的閾值告警不夠用？

大多數團隊的告警規則長這樣：

```yaml
- alert: DiskSpaceHigh
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
  for: 5m
  labels:
    severity: critical
```

問題在於：當磁碟剩餘空間低於 10% 時才告警，往往已經太晚了。如果你的服務每小時寫入 5GB 日誌，而磁碟只剩 10GB，你只有 2 小時的反應時間——而且這可能發生在凌晨。

真正有效的 Capacity Planning 應該回答的問題是：「按照目前的趨勢，這個資源什麼時候會耗盡？」

## 使用 predict_linear 函數預測資源耗盡時間

Prometheus 提供了 `predict_linear` 函數，能根據歷史數據進行線性迴歸預測。以下是一個預測磁碟空間的實用範例：

```yaml
groups:
  - name: capacity_planning
    rules:
      - alert: DiskWillFillIn24Hours
        expr: |
          predict_linear(
            node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[6h], 
            24 * 3600
          ) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "磁碟空間預計在 24 小時內耗盡"
          description: "{{ $labels.instance }} 的 {{ $labels.mountpoint }} 按目前趨勢將在 24 小時內用完"
```

這條規則使用過去 6 小時的數據來預測未來 24 小時的趨勢。`for: 30m` 確保不會因為短暫的寫入高峰產生誤報。

## 記憶體與 CPU 的容量預警策略

對於記憶體，我們關注的不只是當前使用率，而是趨勢：

```yaml
- alert: MemoryPressureIncreasing
  expr: |
    (
      avg_over_time(
        (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)[1h:]
      ) 
      - 
      avg_over_time(
        (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)[1h:] offset 1d
      )
    ) > 0.15
  for: 2h
  labels:
    severity: warning
  annotations:
    summary: "記憶體使用率較昨日同期上升超過 15%"
```

對於 Kubernetes 環境，追蹤 Pod 的資源請求與實際使用的差距同樣重要：

```yaml
- alert: PodMemoryRequestTooLow
  expr: |
    (
      container_memory_working_set_bytes{container!=""}
      / on(namespace, pod, container) 
      kube_pod_container_resource_requests{resource="memory"}
    ) > 0.9
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Pod 記憶體使用率接近 request 值，建議調整"
```

## 建立容量趨勢儀表板

除了告警，建立視覺化儀表板能幫助團隊掌握整體容量狀況。以下是 Grafana 常用的 PromQL 查詢：

```promql
# 計算各節點磁碟預計耗盡天數
(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"})
/ 
(
  (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} offset 7d) 
  - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
) * 7
```

建議在儀表板上顯示以下關鍵指標：
- 各資源的預計耗盡天數（Days Until Exhaustion）
- 過去 7/30 天的資源增長率
- 當前使用率 vs 歷史同期比較

## 結論與行動建議

有效的 Capacity Planning 預警機制應該讓你在問題發生前 24-72 小時就收到通知，而不是在系統崩潰時才驚覺。

**建議的下一步行動：**

1. 立即在你的 Prometheus 中加入 `predict_linear` 告警規則
2. 為不同嚴重程度設定不同的預測時間窗口（72h/24h/4h）
3. 每月檢視告警的準確率，根據實際情況調整參數
4. 將容量趨勢納入每週團隊檢視會議的議程

記住：好的 Capacity Planning 不是要預測得多準確，而是要給你足夠的反應時間。從今天開始，讓監控系統成為你的盟友，而不是半夜叫醒你的敵人。

---
date: 2026-03-24
topic: Capacity Planning
tags: [devops, prometheus, monitoring, alerting, kubernetes, capacity-planning]
---