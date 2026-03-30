# 用 Load Testing 驗證 Capacity Planning：從 k6 實戰掌握系統真實極限

## 前言

Capacity Planning 做得再漂亮，如果沒有經過實際驗證，終究只是紙上談兵。我曾見過團隊根據理論計算預估系統能承受 5000 RPS，上線後卻在 2000 RPS 就開始噴 502 錯誤。問題出在哪？忽略了資料庫連線池耗盡、GC 停頓、網路延遲等實際因素。

本文將聚焦於如何透過 Load Testing 來驗證與校準你的 Capacity Planning，並以 Grafana k6 作為主要工具，帶你建立一套可重複執行的驗證流程。

## 為什麼 Capacity Planning 需要 Load Testing 驗證

理論計算通常基於單一資源的線性推估：CPU 使用率 50% 時處理 1000 RPS，所以 100% 應該能處理 2000 RPS。但現實中，系統瓶頸往往出現在你意想不到的地方：

- 連線池達到上限後的排隊延遲
- 記憶體壓力觸發頻繁 GC
- 下游服務的 Rate Limiting
- Kubernetes HPA 擴展速度跟不上流量增長

Load Testing 能讓你在可控環境中找出這些隱藏瓶頸，將「預估容量」轉化為「實測容量」。

## 設計驗證導向的 Load Test 腳本

驗證 Capacity Planning 的 Load Test 與一般壓測不同，重點在於找出系統的「轉折點」——從健康狀態轉為降級的臨界值。以下是一個使用 k6 的階梯式負載腳本：

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // 暖機階段
    { duration: '5m', target: 500 },   // 預估容量的 50%
    { duration: '5m', target: 800 },   // 預估容量的 80%
    { duration: '5m', target: 1000 },  // 預估容量 100%
    { duration: '5m', target: 1200 },  // 超載測試 120%
    { duration: '3m', target: 0 },     // 冷卻階段
  ],
  thresholds: {
    http_req_duration: ['p95<500'],    // P95 延遲低於 500ms
    http_req_failed: ['rate<0.01'],    // 錯誤率低於 1%
  },
};

export default function () {
  const res = http.get('https://api.example.com/health');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'latency < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

關鍵設計要點：階段式逐步增加負載，讓你能清楚觀察系統在哪個階段開始出現性能降級。

## 整合監控數據進行交叉分析

單看 k6 輸出不夠，你需要同時觀察系統內部指標。建議將 k6 metrics 輸出至 Prometheus，再用 Grafana 建立整合儀表板：

```bash
# 啟動 k6 並輸出 metrics 至 Prometheus
k6 run --out experimental-prometheus-rw \
  --env K6_PROMETHEUS_RW_SERVER_URL=http://prometheus:9090/api/v1/write \
  load_test.js
```

在 Grafana 中建立儀表板，並排呈現以下指標：

| 指標來源 | 關鍵指標 |
|---------|---------|
| k6 | `k6_http_req_duration`、`k6_vus`、`k6_http_reqs` |
| 應用層 | Request latency、Error rate、Active connections |
| 基礎設施 | CPU、Memory、Network I/O |
| 資料庫 | Connection pool usage、Query latency |

當 k6 顯示延遲飆升時，交叉比對其他指標，快速定位是 CPU 滿載、連線池耗盡，還是下游服務拖累。

## 建立可重複的驗證 Pipeline

Capacity Planning 不是一次性工作，每次重大變更後都應重新驗證。將 Load Test 整合進 CI/CD：

```yaml
# .gitlab-ci.yml 範例
load_test:
  stage: performance
  image: grafana/k6:latest
  script:
    - k6 run --out json=results.json scripts/capacity_validation.js
    - python3 scripts/analyze_results.py results.json
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/  # 只在 release tag 時執行
  artifacts:
    paths:
      - results.json
    expire_in: 30 days
```

搭配一個簡單的分析腳本，自動判斷測試結果是否符合容量預期：

```python
import json
import sys

with open(sys.argv[1]) as f:
    data = [json.loads(line) for line in f if line.strip()]

p95_values = [d['data']['value'] for d in data 
              if d.get('metric') == 'http_req_duration' 
              and d.get('data', {}).get('tags', {}).get('percentile') == '95']

if max(p95_values) > 500:
    print(f"FAIL: P95 latency exceeded 500ms (max: {max(p95_values):.2f}ms)")
    sys.exit(1)
print("PASS: Capacity validation successful")
```

## 結論與行動建議

Capacity Planning 的價值在於「可執行」與「可驗證」。我建議你立即採取以下行動：

1. **建立基準線**：在當前流量下執行一次完整壓測，記錄各資源的使用狀況
2. **定義 SLO 閾值**：明確寫下 P95 延遲、錯誤率等可量化指標
3. **自動化驗證流程**：將壓測腳本納入 CI/CD，確保每次 release 前自動執行
4. **定期校準**：至少每季重新執行一次完整壓測，根據結果調整容量規劃

記住：沒有經過壓測驗證的 Capacity Planning，只是一份昂貴的猜測文件。

---
date: 2026-03-30
topic: Capacity Planning
tags: [devops, load-testing, k6, performance, sre, capacity-planning]
---