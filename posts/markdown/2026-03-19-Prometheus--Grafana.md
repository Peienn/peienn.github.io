# Prometheus + Grafana：從零建立完整監控儀表板，打造 Production-Ready 的可觀測性架構

## 前言

在現代微服務架構中，「你無法改善你無法測量的東西」這句話比以往更加重要。當系統從單體架構演進到數十甚至數百個服務時，傳統的日誌檢查方式已經無法滿足即時監控的需求。

Prometheus 與 Grafana 的組合已成為業界標準的開源監控解決方案。Prometheus 負責收集與儲存時間序列資料，Grafana 則提供強大的視覺化能力。本文將帶領你從零開始，建立一套完整的監控儀表板系統，涵蓋安裝部署、資料收集、查詢語法到儀表板設計的完整流程。

## 使用 Docker Compose 快速部署監控堆疊

首先，我們使用 Docker Compose 一次部署 Prometheus、Grafana 與 Node Exporter。建立 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.50.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  grafana:
    image: grafana/grafana:10.3.0
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
    volumes:
      - grafana_data:/var/lib/grafana

  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'

volumes:
  prometheus_data:
  grafana_data:
```

接著建立 Prometheus 設定檔 `prometheus/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

執行 `docker-compose up -d` 即可啟動整個監控堆疊。

## 掌握 PromQL 核心查詢語法

PromQL 是 Prometheus 的查詢語言，掌握它是建立有效儀表板的關鍵。以下是幾個實用的查詢範例：

```promql
# CPU 使用率（排除 idle 狀態）
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 記憶體使用百分比
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# 磁碟使用率
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# 網路流量（每秒接收 bytes）
irate(node_network_receive_bytes_total{device="eth0"}[5m])
```

關鍵函數說明：
- `rate()`：計算每秒平均增長率，適合較長時間範圍
- `irate()`：計算瞬時增長率，適合即時監控
- `avg()`、`sum()`、`max()`：聚合運算子

## 設計 Grafana 儀表板最佳實踐

登入 Grafana（預設 `http://localhost:3000`）後，首先新增 Prometheus 資料來源。進入 **Configuration → Data Sources → Add data source**，選擇 Prometheus 並設定 URL 為 `http://prometheus:9090`。

建立儀表板時，建議遵循以下結構：

1. **Overview Row**：放置關鍵 Stat Panel，一眼掌握系統健康狀態
2. **Resource Usage Row**：CPU、記憶體、磁碟的時間序列圖表
3. **Network Row**：網路流入/流出流量
4. **Alert Status Row**：顯示當前告警狀態

以 JSON 模型定義變數，實現多主機切換：

```json
{
  "name": "instance",
  "type": "query",
  "query": "label_values(node_uname_info, instance)",
  "refresh": 2
}
```

在查詢中使用 `$instance` 變數，例如：`node_memory_MemTotal_bytes{instance="$instance"}`

## 配置告警規則實現主動監控

在 `prometheus/alert_rules.yml` 中定義告警規則：

```yaml
groups:
  - name: node_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes."

      - alert: DiskSpaceLow
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 85
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disk space is running low"
```

更新 `prometheus.yml` 載入規則檔：

```yaml
rule_files:
  - "alert_rules.yml"
```

## 結論與行動建議

完成上述步驟後，你已擁有一套功能完整的監控系統。建議的下一步行動：

1. **整合 Alertmanager**：配置 Slack 或 PagerDuty 通知，實現告警自動化
2. **導入社群 Dashboard**：從 Grafana Labs 官網匯入現成的 Dashboard（如 Node Exporter Full，ID: 1860）
3. **實施 Service Discovery**：針對 Kubernetes 環境，改用動態服務發現取代靜態配置
4. **建立 SLO Dashboard**：基於 SLI 指標追蹤服務水準目標

監控不是一次性任務，而是持續迭代的過程。從這個基礎架構開始，根據實際營運需求逐步擴展，你將建立起真正符合團隊需求的可觀測性平台。

---
date: 2026-03-19
topic: Prometheus + Grafana：從零建立完整監控儀表板
tags: [devops, prometheus, grafana, monitoring, observability, docker]
---