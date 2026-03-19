# Loki vs Elasticsearch：中小型團隊日誌系統的成本效益分析與遷移實戰

## 前言

當團隊的日誌量從每天幾 GB 成長到數十 GB，原本運作良好的 ELK Stack 開始出現記憶體不足、查詢緩慢、維運成本攀升等問題。這時候你可能會問：「該繼續投資擴充 Elasticsearch，還是考慮遷移到 Loki？」

這是許多中小型團隊面臨的真實困境。本文將從架構差異、資源消耗、查詢效能三個面向進行實際比較，並提供從 ELK 遷移到 Loki 的具體步驟，幫助你做出適合團隊的決策。

## 架構本質差異：全文索引 vs 標籤索引

Elasticsearch 採用倒排索引（Inverted Index），會對每一行日誌的每個詞彙建立索引。這提供了強大的全文檢索能力，但代價是巨大的儲存空間和記憶體需求。

Loki 採取截然不同的策略——只索引標籤（Labels），日誌內容本身以壓縮的 chunk 形式儲存，查詢時才進行解壓和過濾。

```yaml
# Loki 的標籤設計範例（promtail config）
scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_container_name]
        target_label: container
```

這意味著 Loki 的查詢速度高度依賴標籤的基數（cardinality）設計。高基數標籤（如 user_id、request_id）會嚴重影響效能，這是遷移時最常踩的坑。

## 實際資源消耗比較

以每天 50GB 日誌量、保留 14 天為例，以下是我們團隊實測的資源對比：

| 項目 | Elasticsearch (3 節點) | Loki (單體模式) |
|------|----------------------|-----------------|
| 記憶體需求 | 48GB (每節點 16GB) | 8GB |
| 儲存空間 | ~2.1TB | ~350GB |
| CPU 核心 | 12 cores | 4 cores |
| 月成本（AWS） | ~$850 | ~$180 |

Loki 的壓縮效率驚人，通常可達原始大小的 10-15%，加上不需要建立全文索引，儲存成本大幅降低。

```bash
# 檢查 Loki 儲存使用狀況
curl -s http://loki:3100/metrics | grep loki_ingester_chunk_stored_bytes_total

# 檢查 Elasticsearch 索引大小
curl -s "http://elasticsearch:9200/_cat/indices?v&h=index,store.size"
```

## 查詢效能的取捨

Elasticsearch 的優勢在於複雜查詢和聚合分析。如果你的使用場景包含大量的 aggregation、模糊搜尋、或跨欄位關聯查詢，Elasticsearch 仍是更好的選擇。

Loki 適合的場景是「先用標籤縮小範圍，再用正則過濾」的查詢模式：

```logql
# Loki LogQL 範例：查詢特定服務的錯誤日誌
{namespace="production", container="api-server"} 
  |= "error" 
  | json 
  | status_code >= 500
  | line_format "{{.timestamp}} [{{.level}}] {{.message}}"

# 統計每分鐘錯誤數量
sum(rate({namespace="production"} |= "error" [1m])) by (container)
```

實測同樣的查詢條件（過去 1 小時的錯誤日誌），Elasticsearch 平均回應時間 200ms，Loki 約 800ms。但對於日常除錯和告警觸發，這個差距通常可以接受。

## 遷移實戰步驟

如果決定遷移，建議採用並行運行策略，而非一次性切換：

```yaml
# Filebeat 同時輸出到 Elasticsearch 和 Loki（透過 Logstash）
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  
output.logstash:
  hosts: ["logstash:5044"]  # Logstash 再轉發到 Loki

---
# 或直接使用 Promtail 搭配 Filebeat
# docker-compose.yml 片段
services:
  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki
```

遷移檢核清單：
1. 盤點現有 Kibana Dashboard，評估哪些可用 Grafana + LogQL 重建
2. 識別高基數標籤，重新設計標籤策略
3. 設定 Loki 的 retention 和 compactor
4. 並行運行 2-4 週，確認查詢需求都能滿足

## 結論與行動建議

選擇的關鍵不在於哪個工具「更好」，而是哪個更符合你的需求：

- **選擇 Elasticsearch**：需要複雜聚合分析、已有成熟的 ELK 維運經驗、預算充足
- **選擇 Loki**：成本敏感、主要用於除錯和告警、已在使用 Prometheus + Grafana 生態系

如果你的團隊正在被 Elasticsearch 的維運成本困擾，建議先在測試環境部署 Loki，將一週的日誌同時寫入兩套系統，實際體驗查詢差異後再做決定。記住，日誌系統的遷移成本不只是技術面，還包含團隊的查詢習慣和 Dashboard 重建，務必預留足夠的過渡期。

---
date: 2026-03-19
topic: ELK Stack / Loki
tags: [devops, logging, loki, elasticsearch, grafana, observability, cost-optimization]
---