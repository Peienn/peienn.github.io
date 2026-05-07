# 第七篇：部署策略與變更管理

前幾篇討論的都是系統**運作時**的可靠性。
這篇討論另一個同樣重要的問題：

> **怎麼在不中斷服務的情況下，把新版本推上去？**

根據 Google SRE 的統計，**70% 的生產事故是由變更引起的**。
部署是系統最脆弱的時刻，設計不良的部署策略會讓每次上線都是一場賭博。

---

## 為什麼部署危險？

```
你在本機測試通過
  ↓
推上 production
  ↓
新版本有一個 bug 在特定條件下觸發
  ↓
所有用戶同時看到錯誤
  ↓
你需要緊急回滾
  ↓
回滾期間服務中斷
```

問題不只是 bug，**回滾本身也可能造成中斷**。

---

## 部署策略比較

### 策略一：Recreate（停機部署）

最簡單，但最危險：

```
停掉舊版本 → 部署新版本 → 啟動

中斷時間 = 停機時間 + 啟動時間
```

**只適合**：開發環境、用戶量極少的服務、深夜維護窗口。

---

### 策略二：Rolling Deploy（滾動部署）

逐台替換，不停機：

```
4 台 Server，新版本逐台替換：

Server1: v1 → v2  （其他三台繼續服務）
Server2: v1 → v2  （其他兩台繼續服務）
Server3: v1 → v2  （Server4 繼續服務）
Server4: v1 → v2  （完成）
```

**優點**：零停機
**缺點**：部署期間新舊版本同時存在，如果 API 有不相容的改動會出問題

聊天室的 Docker Compose 模擬：

```yaml
# docker-compose.yml
services:
  backend:
    image: chatroom-backend:v2  # 改成新版本
    deploy:
      replicas: 2
      update_config:
        parallelism: 1          # 每次更新 1 台
        delay: 10s              # 等 10 秒再更新下一台
        failure_action: rollback # 失敗自動回滾
```

```bash
# 滾動更新
docker compose up -d --no-deps backend
```

---

### 策略三：Blue/Green Deploy（藍綠部署）

同時維護兩套環境：

```
Blue（目前 production）：v1
Green（新版本）：v2

步驟：
1. Green 環境部署 v2
2. 測試 Green 環境
3. Nginx 切換流量：Blue → Green
4. 觀察 5 分鐘
5. 沒問題 → Blue 可以關掉或留著備用
   有問題 → 立刻切回 Blue（秒級回滾）
```

**優點**：回滾最快，切換一個 Nginx 設定就好
**缺點**：需要兩倍的資源

Nginx 切換設定：

```nginx
# nginx.conf

upstream chatroom_blue {
  server backend-blue:3000;
}

upstream chatroom_green {
  server backend-green:3000;
}

server {
  listen 8080;

  location /api {
    # 切換這一行就能在 blue 和 green 之間切換
    proxy_pass http://chatroom_green;
    # proxy_pass http://chatroom_blue;
  }
}
```

```bash
# 熱重載 Nginx，不中斷連線
docker exec my-nginx nginx -s reload
```

---

### 策略四：Canary Deploy（金絲雀部署）

先讓少量用戶使用新版本，觀察沒問題再全量：

```
100% 流量 → v1

Canary 部署後：
5% 流量  → v2（觀察）
95% 流量 → v1

v2 沒問題，逐步增加：
20% → v2
50% → v2
100% → v2
```

**優點**：風險最低，有問題只影響少數用戶
**缺點**：需要流量分配的基礎設施，實作最複雜

Nginx 簡單模擬 Canary：

```nginx
upstream chatroom_v1 {
  server backend-v1:3000 weight=19;  # 95% 流量
}

upstream chatroom_v2 {
  server backend-v2:3000 weight=1;   # 5% 流量
}

server {
  listen 8080;

  location /api {
    proxy_pass http://chatroom_v1;
  }
}
```

---

## 部署時要觀察什麼

部署後的觀察窗口（通常 5～15 分鐘）：

在 Grafana 盯著這幾個指標：

```
✅ HTTP 成功率 → 有沒有突然下降？
✅ p95 回應時間 → 有沒有變慢？
✅ 錯誤率 → 有沒有新的 5xx？
✅ WebSocket 連線數 → 有沒有異常斷線？
✅ Node.js Event Loop Lag → 新版本有沒有引入效能問題？
```

---

## Feature Flag（功能開關）

比部署策略更細緻的控制方式：

```javascript
// config/features.js
const features = {
  aiAnalysis: process.env.FEATURE_AI_ANALYSIS === 'true',
  newChatUI: process.env.FEATURE_NEW_CHAT_UI === 'true',
};

// 使用
if (features.aiAnalysis) {
  await triggerAnalysisOnce(io);
}
```

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      FEATURE_AI_ANALYSIS: "true"
      FEATURE_NEW_CHAT_UI: "false"  # 新 UI 還沒準備好，先關掉
```

Feature Flag 的好處：

- 程式碼可以部署，但功能不一定要開啟
- 出問題只要改環境變數，不用回滾整個部署
- 可以針對特定用戶開啟（A/B Testing）

---

## 變更管理的原則

**原則一：小批次、高頻率**

```
❌ 每個月部署一次，一次改很多東西
✅ 每週部署幾次，每次只改一件事
```

改動越小，出問題時越容易找到原因，回滾的代價也越小。

**原則二：部署要可回滾**

每次部署之前，先確認：
- 這個改動可以回滾嗎？
- 資料庫 migration 有沒有 rollback script？
- 如果要回滾，需要多少時間？

**原則三：部署要可觀測**

部署後你要能立刻知道有沒有出問題。
這就是為什麼第三篇要先建立監控，監控是部署的前提條件。

**原則四：避免在高峰期部署**

聊天室的高峰期可能是晚上，選擇**低峰時段**部署，萬一出問題影響的用戶最少。

---

## 你的聊天室部署策略建議

根據你目前的架構（Docker Compose，兩台 backend）：

**日常部署：Rolling Deploy**

```bash
# 更新 docker-compose.yml 的 image tag
# 然後執行滾動更新
docker compose up -d --no-deps backend
```

**重大改動：Blue/Green Deploy**

改動 API 格式、資料庫 Schema 這類有風險的改動，用 Blue/Green。

**新功能：Feature Flag**

新功能先用 Feature Flag 關起來部署，確認系統穩定後再開啟。

---

## 部署策略選擇指南

| 情境 | 建議策略 |
|---|---|
| 修 bug、小改動 | Rolling Deploy |
| API 格式變更 | Blue/Green |
| 新功能上線 | Feature Flag + Canary |
| 緊急 hotfix | Blue/Green（回滾最快）|
| 資料庫 migration | 停機部署（特殊情況）|

---

## 小結

好的部署策略讓你做到兩件事：

1. **快速交付**：頻繁部署，讓功能快速到達用戶手中
2. **安全交付**：出問題時能快速回滾，降低事故的影響

部署不應該是讓工程師緊張的時刻，而是一個有紀律、有監控、有退路的標準流程。

這是 SRE 系列的最後一篇技術實作文章。
下一篇（第八篇），我們會把這整個系列的經驗轉化成面試素材，
討論如何用這個 side project 在 SRE / Platform Engineer 面試中脫穎而出。
