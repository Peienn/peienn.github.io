# 實戰解析：使用 Sliding Window 演算法打造精準的 API Rate Limiting

## 前言

在微服務架構中，API Rate Limiting 是保護系統穩定性的第一道防線。然而，許多團隊在實作時只停留在最基本的 Fixed Window 計數器，卻忽略了它在視窗邊界時可能產生的流量突波問題。想像一下：你設定每分鐘 100 次請求限制，但使用者可能在第 59 秒發送 100 次、第 60 秒又發送 100 次，實際上在 2 秒內湧入 200 次請求——這完全違背了 Rate Limiting 的初衷。

本文將深入探討 Sliding Window 演算法如何解決這個痛點，並提供可直接套用的 Redis 實作方案。

## Fixed Window 的邊界問題

傳統 Fixed Window 做法是將時間切割成固定區間，每個區間獨立計數。這種方式實作簡單，但存在致命缺陷：

```
時間軸：|-------- 第1分鐘 --------|-------- 第2分鐘 --------|
請求：                    [98次]  [97次]
                          ↑ 59秒  ↑ 00秒
                          
實際效果：2秒內湧入 195 次請求，遠超預期的 100/min 限制
```

當惡意使用者或爬蟲程式利用這個特性，可以在極短時間內發送近乎兩倍的請求量，對後端服務造成壓力。

## Sliding Window Log 演算法原理

Sliding Window Log 的核心概念是記錄每一筆請求的時間戳記，判斷時以「當前時間往回推 N 秒」作為動態視窗：

```python
# 概念示意
def is_allowed(user_id, limit, window_seconds):
    current_time = time.time()
    window_start = current_time - window_seconds
    
    # 移除過期的請求記錄
    remove_requests_before(user_id, window_start)
    
    # 計算視窗內的請求數
    request_count = count_requests(user_id, window_start, current_time)
    
    if request_count < limit:
        add_request(user_id, current_time)
        return True
    return False
```

這種方式能確保任意時間點往回看，都不會超過設定的限制。缺點是需要儲存每筆請求記錄，記憶體消耗較大。

## Redis Sorted Set 實作方案

利用 Redis 的 Sorted Set 結構，可以優雅地實現 Sliding Window Log。以下是完整的 Lua Script，確保原子性操作：

```lua
-- rate_limit.lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

-- 移除過期記錄
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- 取得當前視窗內的請求數
local count = redis.call('ZCARD', key)

if count < limit then
    -- 使用 now + 隨機數確保 score 唯一性
    redis.call('ZADD', key, now, now .. '-' .. math.random())
    redis.call('EXPIRE', key, window)
    return 1
else
    return 0
end
```

在應用程式中呼叫：

```python
import redis
import time

r = redis.Redis(host='localhost', port=6379)
script = r.register_script(open('rate_limit.lua').read())

def check_rate_limit(user_id: str, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}"
    now = int(time.time() * 1000)  # 毫秒精度
    result = script(keys=[key], args=[limit, window * 1000, now])
    return result == 1
```

## 進階優化：Sliding Window Counter

當 QPS 極高時，儲存每筆請求的 Log 方式會消耗大量記憶體。Sliding Window Counter 是一個折衷方案，結合兩個相鄰 Fixed Window 的計數，透過加權計算近似值：

```python
def sliding_window_counter(user_id: str, limit: int, window: int) -> bool:
    now = time.time()
    current_window = int(now // window)
    previous_window = current_window - 1
    
    # 計算當前時間在視窗中的位置比例
    elapsed = now % window
    weight = (window - elapsed) / window
    
    prev_count = redis.get(f"count:{user_id}:{previous_window}") or 0
    curr_count = redis.get(f"count:{user_id}:{current_window}") or 0
    
    # 加權計算
    estimated = int(prev_count) * weight + int(curr_count)
    
    return estimated < limit
```

這種方式只需要儲存兩個計數器，記憶體效率大幅提升，且誤差通常在可接受範圍內。

## 監控指標與告警設定

完成實作後，務必建立對應的監控機制。以下是建議追蹤的 Prometheus 指標：

```yaml
# prometheus-rules.yml
groups:
  - name: rate_limiting
    rules:
      - alert: HighRateLimitRejection
        expr: |
          sum(rate(rate_limit_rejected_total[5m])) 
          / sum(rate(rate_limit_requests_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Rate limit 拒絕率超過 10%"
```

同時在 Grafana 建立儀表板，追蹤各 endpoint 的限流觸發頻率，作為調整閾值的依據。

## 結論與行動建議

選擇 Rate Limiting 演算法時，需要在精確度與資源消耗間取得平衡。建議的行動方案：

1. **評估現況**：檢視目前系統是否使用 Fixed Window，是否曾發生邊界突波問題
2. **選擇策略**：一般場景使用 Sliding Window Counter；需要精確控制時採用 Sliding Window Log
3. **漸進部署**：先以 dry-run 模式收集數據，確認閾值合理後再啟用阻擋
4. **持續監控**：建立告警機制，定期檢視限流觸發的模式是否符合預期

記住，Rate Limiting 不只是技術實作，更是對服務品質的承諾——對合法使用者確保公平性，對惡意行為築起防線。

---
date: 2026-05-03
topic: API Rate Limiting
tags: [devops, rate-limiting, redis, algorithms, backend, sre]
---