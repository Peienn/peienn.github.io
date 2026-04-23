# 解決 RabbitMQ 消費端重複消費問題：實戰冪等性設計指南

## 前言

在分散式系統中，Message Queue 是解耦服務的核心元件，但「消息被重複消費」卻是每位工程師遲早會遇到的惡夢。想像一下：用戶只下了一筆訂單，系統卻扣了兩次款項；或是同一封通知信被發送了三遍。這些問題的根源往往來自於 Message Queue 的「至少一次送達」(At-Least-Once Delivery) 機制。

本文將以 RabbitMQ 為例，深入探討重複消費的成因，並提供三種實戰冪等性設計方案，幫助你在生產環境中徹底解決這個問題。

## 為什麼消息會被重複消費？

RabbitMQ 預設採用 At-Least-Once 語意，當以下情況發生時，同一則消息可能被重複投遞：

1. **Consumer ACK 遺失**：消費端處理完成但在回傳 ACK 前崩潰
2. **網路抖動**：ACK 封包在傳輸途中遺失
3. **消費超時**：處理時間過長導致 RabbitMQ 重新投遞

```bash
# 查看 RabbitMQ 中 unacked 消息數量
rabbitmqctl list_queues name messages_ready messages_unacknowledged
```

當 `messages_unacknowledged` 持續累積，且伴隨 Consumer 重啟，就是重複消費的高風險時刻。

## 方案一：基於 Redis 的消息去重

最直接的做法是利用 Redis 記錄已處理過的消息 ID，在消費前先檢查是否存在：

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)
DEDUP_KEY_PREFIX = "mq:dedup:"
DEDUP_TTL = 86400  # 24 小時過期

def consume_message(channel, method, properties, body):
    message = json.loads(body)
    message_id = properties.message_id
    
    dedup_key = f"{DEDUP_KEY_PREFIX}{message_id}"
    
    # SETNX 確保原子性檢查
    if not redis_client.set(dedup_key, "1", nx=True, ex=DEDUP_TTL):
        print(f"重複消息，跳過處理: {message_id}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    
    try:
        process_business_logic(message)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        redis_client.delete(dedup_key)  # 處理失敗時移除標記
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

**注意事項**：務必為去重 Key 設定 TTL，避免 Redis 記憶體無限增長。

## 方案二：資料庫唯一約束保護

對於訂單、交易等關鍵業務，建議在資料庫層加上唯一約束作為最後防線：

```sql
-- 建立處理紀錄表
CREATE TABLE message_process_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id VARCHAR(64) NOT NULL,
    business_type VARCHAR(32) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_message_id (message_id, business_type)
);
```

```python
def process_with_db_dedup(message_id: str, business_type: str, callback):
    try:
        with db.transaction():
            # INSERT 會因唯一約束失敗而自動去重
            db.execute(
                "INSERT INTO message_process_log (message_id, business_type) VALUES (%s, %s)",
                (message_id, business_type)
            )
            callback()
    except DuplicateKeyError:
        print(f"資料庫層攔截重複消息: {message_id}")
```

此方案的優勢是即使 Redis 故障，資料庫仍能確保冪等性。

## 方案三：業務狀態機設計

對於有明確狀態流轉的業務（如訂單），設計狀態機是最優雅的解法：

```python
# 訂單狀態流轉：CREATED -> PAID -> SHIPPED -> COMPLETED

def handle_payment_message(order_id: str, payment_info: dict):
    order = Order.query.filter_by(id=order_id).with_for_update().first()
    
    # 狀態檢查：只有 CREATED 狀態才能轉為 PAID
    if order.status != OrderStatus.CREATED:
        print(f"訂單 {order_id} 狀態為 {order.status}，忽略重複付款消息")
        return
    
    order.status = OrderStatus.PAID
    order.paid_at = datetime.now()
    order.payment_info = payment_info
    db.session.commit()
```

搭配 `SELECT ... FOR UPDATE` 悲觀鎖，確保並發情況下的狀態一致性。

## 監控與告警配置

實作冪等性後，建議加入以下監控指標：

```yaml
# Prometheus 告警規則範例
groups:
  - name: rabbitmq_duplicate_alerts
    rules:
      - alert: HighDuplicateMessageRate
        expr: |
          rate(message_duplicate_total[5m]) / rate(message_consumed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "重複消息比例超過 10%，請檢查上游 Producer 或網路狀況"
```

## 結論與行動建議

防止重複消費的核心思想是「讓同一操作執行多次與執行一次的結果相同」。根據業務場景選擇適當方案：

1. **高吞吐量場景**：優先採用 Redis 去重，搭配合理 TTL
2. **金融級業務**：Redis + 資料庫唯一約束雙重保護
3. **狀態型業務**：設計完整狀態機，從根本杜絕問題

建議下一步行動：檢視你目前的 Consumer 程式碼，確認是否有處理重複消費的機制。若沒有，先從 Redis 去重方案開始實作，這是成本最低且效果顯著的起手式。

---
date: 2026-04-23
topic: Message Queue
tags: [devops, rabbitmq, idempotency, redis, distributed-systems]
---