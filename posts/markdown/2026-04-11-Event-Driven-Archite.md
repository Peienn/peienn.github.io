# Event-Driven Architecture 中的訊息遺失問題：實戰防禦策略與實作

## 前言

在導入 Event-Driven Architecture（EDA）後，許多團隊很快就會遇到一個棘手的問題：**訊息遺失**。當你的訂單事件在某個環節消失、用戶通知莫名其妙沒送出、或是資料同步出現不一致時，除錯過程往往令人崩潰。這不僅影響系統可靠性，更可能造成實際的商業損失。

對於已經熟悉基本 EDA 概念的中階 DevOps 工程師來說，理解訊息遺失的常見原因與對應的防禦策略，是讓系統從「能動」進化到「穩定」的關鍵一步。本文將從實務角度出發，探討幾種常見的訊息遺失情境，並提供具體的解決方案與程式碼範例。

## 訊息遺失的三大常見情境

在典型的 EDA 架構中，訊息遺失通常發生在以下三個環節：

1. **Producer 端遺失**：訊息還沒成功寫入 Message Broker 就發生錯誤
2. **Broker 端遺失**：Broker 接收訊息後，因故障或設定問題導致遺失
3. **Consumer 端遺失**：Consumer 取得訊息後處理失敗，但訊息已被確認（ACK）

以 RabbitMQ 為例，你可以用以下指令監控 unacknowledged 訊息數量，及早發現潛在問題：

```bash
# 查看特定 queue 的訊息狀態
rabbitmqctl list_queues name messages_ready messages_unacknowledged

# 或使用 Management API
curl -u guest:guest http://localhost:15672/api/queues/%2F/your_queue_name
```

## 使用 Publisher Confirms 確保訊息送達

Producer 端最有效的防護機制是啟用 **Publisher Confirms**。這能確保訊息確實被 Broker 接收並持久化後，才視為發送成功。

以下是 Python 搭配 `pika` 的實作範例：

```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# 啟用 publisher confirms
channel.confirm_delivery()

# 宣告持久化 queue
channel.queue_declare(queue='orders', durable=True)

try:
    channel.basic_publish(
        exchange='',
        routing_key='orders',
        body='{"order_id": "12345"}',
        properties=pika.BasicProperties(
            delivery_mode=2,  # 訊息持久化
        ),
        mandatory=True  # 確保訊息能路由到 queue
    )
    print("訊息已確認送達")
except pika.exceptions.UnroutableError:
    print("訊息無法路由，需進行補償處理")
```

關鍵設定包含：`confirm_delivery()` 啟用確認機制、`delivery_mode=2` 持久化訊息、`mandatory=True` 確保可路由。

## 實作 Dead Letter Queue 處理失敗訊息

Consumer 端處理失敗時，直接丟棄訊息是最糟的做法。透過 **Dead Letter Queue（DLQ）**，可以將處理失敗的訊息轉移到專用 queue 進行後續分析或重試。

```bash
# 建立 DLQ 與主要 queue 的設定
rabbitmqadmin declare queue name=orders_dlq durable=true

rabbitmqadmin declare queue name=orders durable=true \
    arguments='{"x-dead-letter-exchange": "", "x-dead-letter-routing-key": "orders_dlq"}'
```

搭配 Consumer 端的手動 ACK 機制：

```python
def callback(ch, method, properties, body):
    try:
        process_order(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # 拒絕訊息且不重新入隊，讓它進入 DLQ
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        log_error(e)

channel.basic_consume(queue='orders', on_message_callback=callback)
```

## 建立端對端的訊息追蹤機制

當系統規模擴大，光靠單點監控已不足夠。導入 **Correlation ID** 與分散式追蹤工具（如 Jaeger、Zipkin）能幫助你追蹤每則訊息的完整生命週期。

```python
import uuid

def publish_event(channel, event_data):
    correlation_id = str(uuid.uuid4())
    
    channel.basic_publish(
        exchange='events',
        routing_key='user.created',
        body=json.dumps(event_data),
        properties=pika.BasicProperties(
            correlation_id=correlation_id,
            headers={'trace_id': correlation_id}
        )
    )
    
    # 記錄到集中式日誌
    logger.info(f"Event published", extra={
        'correlation_id': correlation_id,
        'event_type': 'user.created'
    })
```

搭配 ELK Stack 或 Grafana Loki，你可以快速查詢特定訊息的流向：

```bash
# Elasticsearch 查詢範例
curl -X GET "localhost:9200/logs/_search?q=correlation_id:abc123"
```

## 結論與行動建議

訊息遺失是 Event-Driven Architecture 中無法完全避免、但可以有效控制的風險。建議你依照以下優先順序進行改善：

1. **立即執行**：為所有 Producer 啟用 Publisher Confirms，確保訊息持久化
2. **短期目標**：為關鍵 queue 配置 Dead Letter Queue，避免失敗訊息直接消失
3. **中期規劃**：導入 Correlation ID 與集中式日誌，建立端對端追蹤能力
4. **持續監控**：設定 unacknowledged 訊息數量告警，及早發現 Consumer 處理瓶頸

記住，在分散式系統中，「假設一切都會失敗」是最務實的設計原則。預先建立好防禦機制，才能在問題發生時從容應對。

---
date: 2026-04-11
topic: Event-Driven Architecture
tags: [devops, message-queue, rabbitmq, reliability, distributed-systems]
---