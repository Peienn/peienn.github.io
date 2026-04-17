# Loki vs Elasticsearch：輕量級日誌方案如何降低 80% 儲存成本

## 前言

當團隊的微服務數量從 10 個成長到 50 個，日誌量也跟著爆炸性成長。許多 DevOps 工程師會發現，原本運作良好的 ELK Stack 突然變成吃錢怪獸——Elasticsearch 叢集需要不斷擴充節點、記憶體和儲存空間。

這時候你可能會問：有沒有更輕量的替代方案？

Grafana Loki 正是為了解決這個痛點而生。它採用與 Elasticsearch 完全不同的設計哲學：只索引 metadata，不索引日誌內容。本文將從實務角度比較兩者的架構差異、部署複雜度與成本效益，幫助你判斷何時該考慮從 ELK 遷移到 Loki。

## 架構差異：全文索引 vs 標籤索引

Elasticsearch 的核心優勢在於全文索引（Full-text Indexing），每一行日誌的每個詞都會被分析並建立倒排索引。這讓搜尋速度極快，但代價是龐大的索引儲存空間。

```
# Elasticsearch 典型的索引與原始資料比例
原始日誌：100 GB
索引大小：約 100-150 GB
總儲存需求：200-250 GB
```

Loki 則採用完全不同的策略，它只對 labels（標籤）建立索引：

```yaml
# Loki 的日誌串流定義
{job="nginx", env="production", instance="web-01"}
```

日誌內容本身會被壓縮後直接儲存到物件儲存（如 S3、GCS），查詢時才進行暴力掃描。

```
# Loki 的儲存比例
原始日誌：100 GB
壓縮後儲存：約 15-25 GB（使用 gzip/snappy）
索引大小：約 1-2 GB
總儲存需求：20-30 GB
```

## 部署複雜度比較

部署一套生產級 ELK Stack，你至少需要：

```yaml
# ELK 最小生產部署
elasticsearch:
  master_nodes: 3
  data_nodes: 3
  coordinating_nodes: 2
  memory_per_node: 16-32 GB

logstash:
  instances: 2
  memory_per_instance: 4-8 GB

kibana:
  instances: 2
```

相比之下，Loki 的架構簡潔許多。使用單體模式（Monolithic Mode）甚至可以單節點運行：

```bash
# 使用 Docker 快速部署 Loki
docker run -d --name loki -p 3100:3100 \
  -v /path/to/loki-config.yaml:/etc/loki/local-config.yaml \
  grafana/loki:2.9.0 \
  -config.file=/etc/loki/local-config.yaml
```

搭配 Promtail 作為日誌收集器：

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*log.json
```

## 查詢語法與使用場景

Elasticsearch 使用 Lucene 語法或 KQL，適合複雜的全文搜尋：

```
# Kibana KQL 查詢範例
message: "error" AND response_code: 500 AND @timestamp >= "2024-01-01"
```

Loki 使用 LogQL，語法更接近 PromQL：

```logql
# Grafana LogQL 查詢範例
{job="nginx", env="production"} |= "error" | json | status_code = 500
```

關鍵差異在於：Loki 必須先透過 labels 縮小範圍，再進行內容過濾。如果你的使用場景是：

- ✅ 根據服務、環境、實例查詢日誌 → Loki 適合
- ✅ 查看特定時間段的錯誤日誌 → Loki 適合
- ❌ 在所有日誌中搜尋特定關鍵字 → Elasticsearch 更快
- ❌ 複雜的日誌分析與聚合報表 → Elasticsearch 更強

## 實際成本試算

以每日 500 GB 日誌量為例，保留 30 天：

| 項目 | ELK Stack（自建） | Loki + S3 |
|------|------------------|-----------|
| 儲存需求 | ~30 TB（含索引） | ~5 TB |
| 運算節點 | 8+ 節點 | 2-3 節點 |
| 記憶體需求 | 128+ GB | 16-32 GB |
| 月成本估算 | $2,000-3,000 | $400-600 |

```bash
# 計算 S3 儲存成本
# 5TB × $0.023/GB = $115/月（標準儲存）
# 搭配生命週期政策可再降低成本
aws s3api put-bucket-lifecycle-configuration \
  --bucket loki-logs \
  --lifecycle-configuration file://lifecycle.json
```

## 結論與行動建議

Loki 並非要取代 Elasticsearch，而是提供了一個更符合雲原生思維的選擇。如果你的團隊符合以下條件，建議認真評估遷移：

1. **已經使用 Prometheus + Grafana** — Loki 與現有監控堆疊無縫整合
2. **日誌查詢以 label-based 為主** — 不需要頻繁全文搜尋
3. **成本壓力大** — 特別是中小型團隊

實際行動步驟：
1. 先在測試環境部署 Loki，將部分非關鍵服務的日誌導入
2. 讓團隊適應 LogQL 語法，評估查詢體驗
3. 確認可行後，逐步遷移生產環境服務

記住：選擇工具永遠要基於實際需求，而非技術潮流。

---
date: 2026-04-17
topic: ELK Stack / Loki
tags: [devops, logging, loki, elasticsearch, observability, cost-optimization]
---