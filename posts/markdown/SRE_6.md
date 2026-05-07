# 第六篇：容量規劃與壓力測試

前幾篇建立了監控和可靠性設計，但有一個問題還沒有回答：

> **這個系統，最多能撐幾個人？**

容量規劃就是回答這個問題的方法論。

---

## 容量規劃的核心問題

```
1. 系統現在能承受多少負載？
2. 哪個元件會最先到達瓶頸？
3. 如何擴展才能支撐更多用戶？
```

回答這三個問題，需要**壓力測試**和**數據觀察**。

---

## 壓力測試工具：k6

k6 是一個用 JavaScript 寫測試腳本的壓測工具，特別適合 HTTP 和 WebSocket。

安裝：

```bash
brew install k6
```

---

## 第一步：基準測試（Baseline）

在做壓測之前，先建立基準線：系統在**正常負載**下的表現。

```javascript
// baseline-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,        // 1 個虛擬用戶
  duration: '30s',
};

export default function () {
  // 登入
  const loginRes = http.post(
    'http://localhost:80/login',
    JSON.stringify({ username: `baseline_user` }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(loginRes, {
    '登入成功': (r) => r.status === 200,
    '回應時間 < 100ms': (r) => r.timings.duration < 100,
  });

  // 讀取歷史訊息
  const historyRes = http.get('http://localhost:80/api/message/history');

  check(historyRes, {
    '讀取成功': (r) => r.status === 200,
    '回應時間 < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

```bash
k6 run baseline-test.js
```

記錄下這個結果，這是你的**基準線**：
- 登入 API：p95 = ?ms
- 歷史訊息 API：p95 = ?ms

---

## 第二步：負載測試（Load Test）

模擬正常的預期用戶數量，確認系統能穩定運作。

```javascript
// load-test.js
import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // 爬升到 50 人
    { duration: '3m', target: 50 },   // 維持 50 人 3 分鐘
    { duration: '1m', target: 0 },    // 降回 0
  ],
  thresholds: {
    // 定義通過標準
    http_req_duration: ['p(95)<200'],  // p95 < 200ms
    http_req_failed: ['rate<0.01'],    // 錯誤率 < 1%
  },
};

const BASE_URL = 'http://localhost:80';

export default function () {
  const username = `load_user_${__VU}`;

  // 登入
  const loginRes = http.post(
    `${BASE_URL}/login`,
    JSON.stringify({ username }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(loginRes, { '登入成功': (r) => r.status === 200 });

  const cookies = loginRes.cookies['chatroom.sid'];
  if (!cookies || cookies.length === 0) return;

  const cookieStr = `chatroom.sid=${cookies[0].value}`;

  // WebSocket 連線
  const wsRes = ws.connect(
    `ws://localhost:80/socket.io/?EIO=4&transport=websocket`,
    { headers: { Cookie: cookieStr } },
    function (socket) {
      socket.on('open', () => socket.send('2probe'));

      socket.on('message', (data) => {
        if (data === '3probe') socket.send('5');
      });

      // 每 5 秒發一則訊息
      socket.setInterval(() => {
        socket.send(`42["chat-message","VU${__VU} 測試訊息"]`);
      }, 5000);

      socket.setTimeout(() => socket.close(), 30000);
    }
  );

  check(wsRes, { 'WebSocket 連線成功': (r) => r && r.status === 101 });

  sleep(1);
}
```

```bash
k6 run load-test.js
```

---

## 第三步：壓力測試（Stress Test）

找出系統的**破壞點**，超過這個點系統就會開始降級或崩潰。

```javascript
// stress-test.js
export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 300 },
    { duration: '2m', target: 400 },
    { duration: '2m', target: 500 },
    { duration: '2m', target: 0 },
  ],
};
```

觀察在哪個並發數量時，以下指標開始惡化：
- 錯誤率開始上升
- p95 回應時間開始超過 SLO
- Node.js Event Loop Lag 開始增加
- Redis 記憶體快速增長

---

## 第四步：浸泡測試（Soak Test）

驗證系統在**長時間持續負載**下是否有記憶體洩漏或性能衰退。

```javascript
// soak-test.js
export const options = {
  stages: [
    { duration: '5m', target: 50 },   // 爬升
    { duration: '4h', target: 50 },   // 維持 4 小時
    { duration: '5m', target: 0 },    // 降回
  ],
};
```

觀察重點：
- Node.js Heap 有沒有一直增長（記憶體洩漏）
- 回應時間有沒有隨時間惡化
- Redis 連線數有沒有一直增加

---

## 解讀壓測結果

跑完壓測後，對照 Grafana Dashboard 觀察：

### Node.js 視角

```
Event Loop Lag 開始增加
  → Node.js 開始過載
  → 考慮水平擴展（加 Server）

Heap 持續增長不回落
  → 記憶體洩漏
  → 檢查是否有未清除的 listener 或 timer

RSS 記憶體接近容器上限
  → 調高容器 memory limit
  → 或優化記憶體使用
```

### Redis 視角

```
connected_clients 持續增加
  → WebSocket 斷線沒有正確清理 Redis 連線
  → 檢查 disconnect 事件處理

memory_used 接近 maxmemory
  → 設定 maxmemory-policy（eviction 策略）
  → 考慮增加 Redis 記憶體

keyspace_hit_rate 下降
  → Cache 效率降低
  → 檢查 key 的 TTL 設定
```

### PostgreSQL 視角

```
active connections 接近上限
  → 連線池不夠大
  → 增加 pool size 或加入 PgBouncer

idle in transaction 增加
  → 有 transaction 沒有正確 commit
  → 檢查程式碼是否有 try-catch 漏掉 rollback
```

---

## 容量規劃的計算方式

假設你的壓測結果是：

```
每個 Node.js instance：
  最大穩定承載 = 200 個 WebSocket 連線
  CPU 使用率在 200 人時 = 60%

目標：支撐 1000 人同時在線
```

計算需要的 instance 數量：

```
1000 人 ÷ 200 人/instance = 5 個 instance

加上 20% 緩衝：
5 × 1.2 = 6 個 instance
```

這就是你的**容量規劃基準**：要支撐 1000 人，需要 6 個 Node.js instance。

---

## 瓶頸通常在哪裡

根據聊天室的架構，瓶頸最可能出現的地方：

**第一名：Redis（最可能）**

因為所有功能都依賴 Redis，Session、Cache、Pub/Sub 共用一個實例，高並發時 Redis 會最先成為瓶頸。

**第二名：Node.js Event Loop**

JavaScript 是單執行緒，CPU 密集任務會阻塞所有請求。
高並發 WebSocket 時，Event Loop Lag 會快速增加。

**第三名：PostgreSQL 連線數**

PostgreSQL 預設最大連線數是 100，高並發時容易耗盡。
解法：加入 PgBouncer 做連線池。

**最不可能：Nginx**

Nginx 的 C10K 問題早就解決了，同時處理 10000 個連線對 Nginx 來說不是問題。

---

## 小結

容量規劃的結論不是一個數字，而是一份**系統行為的地圖**：

- 在多少並發量以下，系統表現良好
- 超過哪個點，哪個元件最先出問題
- 要支撐更多用戶，應該先擴展哪裡

這份地圖讓你在系統需要擴展時，能做出有依據的工程決策，而不是靠猜測。

下一篇，我們討論部署策略：
怎麼在不中斷服務的情況下，把新版本的程式碼推上生產環境？
