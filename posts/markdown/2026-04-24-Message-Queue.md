# 解決 RabbitMQ 消息堆積問題：從監控到消費者優化的實戰指南

## 前言

在分散式系統中，Message Queue 是解耦服務的關鍵元件。然而，當消費者處理速度跟不上生產者發送速度時，**消息堆積（Message Backlog）** 就會成為系統的隱形殺手。

我曾經歷過一次凌晨三點的 on-call：RabbitMQ 節點記憶體飆升到 95%，導致整個叢集進入 flow control 狀態，上游服務全面阻塞。事後分析發現，這只是因為一個下游服務的資料庫連線池配置不當，導致消費速度驟降。

這篇文章將分享如何**提前發現、快速診斷、有效解決** RabbitMQ 的消息堆積問題，讓你避免成為下一個凌晨被叫醒的人。

## 建立有效的堆積監控告警

解決問題的第一步是能夠及時發現問題。RabbitMQ 提供了豐富的 metrics，我們需要關注的核心指標包括：

- `queue_messages_ready`：等待被消費的消息數量
- `queue_messages_unacknowledged`：已投遞但未確認的消息數量
- `message_publish_rate` vs `message_deliver_rate`：生產與消費速率差異

使用 Prometheus + RabbitMQ Exporter 可以輕鬆收集這些指標：

```yaml
# prometheus-alerts.yml
groups:
  - name: rabbitmq
    rules:
      - alert: RabbitMQMessageBacklog
        expr: rabbitmq_queue_messages_ready > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Queue {{ $labels.queue }} 堆積超過 10000 條消息"
      
      - alert: RabbitMQConsumerDown
        expr: rabbitmq_queue_consumers == 0 and rabbitmq_queue_messages_ready > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Queue {{ $labels.queue }} 無消費者但有待處理消息"
```

建議將告警閾值設定為平常堆積量的 3-5 倍，避免誤報又能及時預警。

## 快速診斷堆積根因

當收到告警時，需要快速定位是生產端暴增還是消費端變慢。使用 `rabbitmqctl` 可以即時獲取 Queue 狀態：

```bash
# 查看指定 queue 的詳細狀態
rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers message_stats.publish_details.rate message_stats.deliver_details.rate

# 輸出範例：
# order_queue  45230  500  3  1200.5  180.2
```

上述輸出顯示 `order_queue` 有 45230 條待處理消息，3 個消費者，生產速率 1200 msg/s，消費速率僅 180 msg/s。問題很明顯：**消費速度嚴重不足**。

接下來檢查消費者端：

```bash
# 查看消費者詳情，包含 prefetch_count 和 ack_required
rabbitmqctl list_consumers queue_name channel_pid ack_required prefetch_count
```

若 `prefetch_count` 設定過低（例如 1），單一消費者的吞吐量會被嚴重限制。

## 調整 Prefetch 與消費者並行度

`prefetch_count` 決定了 RabbitMQ 一次推送多少條消息給消費者。設定過低會導致網路往返延遲放大，設定過高則可能造成消費者記憶體壓力。

以 Python Pika 為例，調整 prefetch 設定：

```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# 將 prefetch 從預設的 0（無限制）調整為合理值
channel.basic_qos(prefetch_count=50)

def callback(ch, method, properties, body):
    process_message(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='order_queue', on_message_callback=callback)
channel.start_consuming()
```

經驗法則：
- **CPU 密集型任務**：prefetch 設為 1-5
- **I/O 密集型任務**：prefetch 設為 20-100
- 搭配消費者內部的 worker pool 效果更佳

同時，透過 Kubernetes HPA 動態擴展消費者數量：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-consumer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-consumer
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: External
      external:
        metric:
          name: rabbitmq_queue_messages_ready
          selector:
            matchLabels:
              queue: order_queue
        target:
          type: AverageValue
          averageValue: "1000"
```

## 設定 Queue TTL 與 Dead Letter 作為最後防線

即使做了上述優化，極端情況下仍可能堆積。為避免記憶體耗盡導致叢集崩潰，應設定 Queue 的訊息過期策略：

```bash
# 建立 Queue 時設定 TTL 和 Dead Letter Exchange
rabbitmqctl declare queue name=order_queue durable=true arguments='{"x-message-ttl": 3600000, "x-dead-letter-exchange": "dlx.order", "x-max-length": 100000}'
```

這樣超過 1 小時未消費或 Queue 長度超過 10 萬條時，舊消息會被轉移到 Dead Letter Queue，供事後補償處理，同時保護主叢集穩定性。

## 結論與行動建議

消息堆積看似是容量問題，實則常反映出系統設計或配置的不足。建議你立即採取以下行動：

1. **今天就部署監控**：確保 `messages_ready` 和消費速率差異有告警覆蓋
2. **Review 你的 prefetch 設定**：很多專案直接用預設值，這通常不是最佳解
3. **加入 Dead Letter 機制**：給系統一個「洩壓閥」，避免雪崩式故障
4. **建立 Runbook**：將診斷步驟和擴容指令文件化，縮短 MTTR

處理消息堆積的最佳時機，是在它發生之前就做好準備。

---
date: 2026-04-24
topic: Message Queue
tags: [devops, rabbitmq, monitoring, performance, distributed-systems]
---