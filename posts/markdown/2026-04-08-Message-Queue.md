# 當 Message Queue 訊息堆積爆量：三種實戰消化策略與監控告警設計

## 前言

身為 DevOps 工程師，你一定遇過這個場景：某天早上收到告警，發現 RabbitMQ 或 Kafka 的訊息堆積數量從平常的幾百筆，暴增到數十萬筆。Consumer 來不及處理，Producer 還在持續塞入，整個系統像塞車的高速公路，動彈不得。

訊息堆積（Message Backlog）是 Message Queue 最常見的生產問題之一。它不只影響系統即時性，嚴重時會導致記憶體耗盡、服務崩潰，甚至資料遺失。本文將分享三種實戰驗證的消化策略，以及如何建立有效的監控告警機制，讓你在問題發生前就能預防，發生時能快速應對。

## 策略一：動態擴展 Consumer 實例

最直覺的解法就是增加 Consumer 的處理能力。但關鍵不是手動加機器，而是建立自動擴展機制。

以 Kubernetes 搭配 KEDA（Kubernetes Event-driven Autoscaling）為例，你可以根據 Queue 深度自動調整 Consumer Pod 數量：

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-consumer-scaler
spec:
  scaleTargetRef:
    name: order-consumer
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:
    - type: rabbitmq
      metadata:
        queueName: orders
        host: amqp://rabbitmq.default.svc.cluster.local:5672
        queueLength: "1000"
```

這個設定會在 `orders` Queue 超過 1000 則訊息時，自動擴展 Consumer Pod，最多到 20 個實例。當堆積消化完畢，Pod 數量會自動縮減，節省資源成本。

## 策略二：批次處理取代逐筆消費

許多 Consumer 採用逐筆處理模式，每收到一則訊息就執行一次資料庫寫入或 API 呼叫。當堆積發生時，這種模式的效率極低。

改用批次處理可以大幅提升吞吐量。以 Python 搭配 Kafka 為例：

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'user-events',
    bootstrap_servers=['kafka:9092'],
    group_id='event-processor',
    enable_auto_commit=False,
    max_poll_records=500  # 每次最多拉取 500 則
)

batch = []
for message in consumer:
    batch.append(json.loads(message.value))
    
    if len(batch) >= 100:
        # 批次寫入資料庫
        bulk_insert_to_database(batch)
        consumer.commit()
        batch = []
```

批次處理能減少網路往返次數與資料庫連線開銷。實務上，從逐筆改為每 100 筆批次處理，吞吐量提升 5 到 10 倍是常見的數字。

## 策略三：設置 Dead Letter Queue 與訊息過期

有時候堆積的原因是 Consumer 遇到無法處理的毒藥訊息（Poison Message），導致不斷重試失敗。這時候需要 Dead Letter Queue（DLQ）來隔離問題訊息。

RabbitMQ 的 DLQ 設定範例：

```bash
# 建立 Dead Letter Exchange
rabbitmqadmin declare exchange name=dlx type=direct

# 建立 Dead Letter Queue
rabbitmqadmin declare queue name=orders-dlq

# 綁定 DLQ
rabbitmqadmin declare binding source=dlx destination=orders-dlq routing_key=orders

# 設定主要 Queue 的 DLQ 與訊息 TTL
rabbitmqadmin declare queue name=orders \
  arguments='{"x-dead-letter-exchange":"dlx","x-dead-letter-routing-key":"orders","x-message-ttl":300000}'
```

這個設定讓訊息在 5 分鐘（300000 毫秒）內未被成功消費，就會自動轉移到 DLQ。你可以事後分析 DLQ 中的訊息，找出問題根因，而不會阻塞正常流程。

## 監控告警：防患於未然

消化策略是事後補救，但更重要的是事前預警。建議監控以下三個關鍵指標：

```yaml
# Prometheus Alert Rules 範例
groups:
  - name: message-queue-alerts
    rules:
      - alert: HighMessageBacklog
        expr: rabbitmq_queue_messages_ready > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Queue {{ $labels.queue }} 訊息堆積超過 10000"
      
      - alert: ConsumerLag
        expr: kafka_consumer_group_lag > 50000
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Kafka Consumer Group {{ $labels.group }} 延遲嚴重"
      
      - alert: DeadLetterQueueGrowing
        expr: increase(rabbitmq_queue_messages_ready{queue=~".*-dlq"}[1h]) > 100
        labels:
          severity: warning
        annotations:
          summary: "DLQ {{ $labels.queue }} 過去一小時增加超過 100 則"
```

這三個告警分別監控：堆積數量、消費延遲、以及 DLQ 異常增長。搭配 Grafana Dashboard 視覺化，能讓團隊即時掌握 Queue 健康狀態。

## 結論與行動建議

訊息堆積是 Message Queue 的必考題，但有正確的策略就能從容應對。建議你：

1. **本週內**：檢視現有 Consumer 是否支援水平擴展，評估導入 KEDA 的可行性
2. **本月內**：審視處理邏輯，找出可改為批次處理的 Consumer
3. **持續維護**：確保所有 Queue 都有對應的 DLQ，並建立完整的監控告警

記住，最好的 Incident Response 是讓 Incident 不要發生。把監控做好，堆積問題就能在萌芽階段被發現並解決。

---
date: 2026-04-08
topic: Message Queue
tags: [devops, rabbitmq, kafka, keda, monitoring, prometheus]
---