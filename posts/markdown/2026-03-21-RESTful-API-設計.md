# RESTful API 設計：善用 HTTP 狀態碼打造清晰的錯誤處理機制

## 前言

在日常維運與開發工作中，我們經常遇到這樣的場景：前端工程師抱怨 API 錯誤訊息不明確、除錯時難以判斷問題來源、或是監控系統無法有效區分不同類型的錯誤。這些問題的根源，往往來自於 API 設計時對 HTTP 狀態碼的誤用或濫用。

許多團隊習慣性地將所有錯誤都回傳 `200 OK` 搭配自定義的錯誤碼，或是過度簡化只使用 `400` 和 `500`。這種做法不僅違反 RESTful 設計原則，更會造成監控告警失準、API Gateway 路由規則失效，以及 Client 端難以實作統一的錯誤處理邏輯。本文將探討如何正確運用 HTTP 狀態碼，建立一套清晰、一致的錯誤處理機制。

## 理解 HTTP 狀態碼的語意分類

HTTP 狀態碼並非隨意選擇的數字，而是具有明確語意的分類系統。作為 DevOps 工程師，理解這些分類對於設定監控告警和日誌分析至關重要：

- **2xx（成功）**：請求已成功處理
- **3xx（重導向）**：需要進一步操作
- **4xx（客戶端錯誤）**：請求本身有問題
- **5xx（伺服器錯誤）**：伺服器處理失敗

在 Prometheus + Grafana 的監控架構中，我們通常會這樣設定告警規則：

```yaml
# prometheus-rules.yaml
groups:
  - name: api-error-rates
    rules:
      - alert: HighClientErrorRate
        expr: sum(rate(http_requests_total{status=~"4.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
      - alert: HighServerErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
        for: 2m
        labels:
          severity: critical
```

如果 API 將錯誤都包裝在 `200` 回應中，這些監控規則將完全失效。

## 常見 4xx 狀態碼的正確使用場景

4xx 狀態碼表示客戶端錯誤，選擇正確的狀態碼能讓 API 使用者快速定位問題：

```python
# Flask 範例：不同場景的狀態碼回應
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # 400 Bad Request - 請求格式錯誤
    if not validate_request_format(request):
        return jsonify({"error": "INVALID_FORMAT", "message": "請求格式不正確"}), 400
    
    # 401 Unauthorized - 未提供認證資訊
    if not request.headers.get('Authorization'):
        return jsonify({"error": "UNAUTHORIZED", "message": "需要認證"}), 401
    
    # 403 Forbidden - 已認證但無權限
    if not has_permission(current_user, user_id):
        return jsonify({"error": "FORBIDDEN", "message": "無權存取此資源"}), 403
    
    # 404 Not Found - 資源不存在
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "NOT_FOUND", "message": "使用者不存在"}), 404
    
    # 409 Conflict - 資源衝突（常用於 PUT/POST）
    # 422 Unprocessable Entity - 語意錯誤（格式正確但內容無法處理）
    
    return jsonify(user.to_dict()), 200
```

## 設計統一的錯誤回應格式

僅有正確的狀態碼還不夠，統一的錯誤回應結構能大幅提升 API 的可維護性：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "輸入資料驗證失敗",
    "details": [
      {
        "field": "email",
        "reason": "格式不正確"
      },
      {
        "field": "age", 
        "reason": "必須為正整數"
      }
    ],
    "trace_id": "abc-123-xyz",
    "timestamp": "2026-03-21T10:30:00Z"
  }
}
```

在 Nginx 層級，我們可以確保即使後端服務異常，也能回傳統一格式：

```nginx
# nginx.conf
error_page 502 503 504 /50x.json;

location = /50x.json {
    internal;
    default_type application/json;
    return 503 '{"error": {"code": "SERVICE_UNAVAILABLE", "message": "服務暫時無法使用"}}';
}
```

## 透過 OpenAPI 規範文件化錯誤回應

將錯誤回應明確記錄在 API 規範中，是團隊協作的關鍵。使用 OpenAPI 3.0 可以清楚定義各種錯誤場景：

```yaml
# openapi.yaml
paths:
  /users/{id}:
    get:
      responses:
        '200':
          description: 成功取得使用者資料
        '401':
          description: 未經授權
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: 使用者不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
components:
  schemas:
    Error:
      type: object
      required: [error]
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            trace_id:
              type: string
```

## 結論與行動建議

正確使用 HTTP 狀態碼不僅是 RESTful 設計的基本要求，更直接影響到監控告警的準確性、API Gateway 的路由策略，以及整體系統的可觀測性。

建議的行動步驟：
1. **盤點現有 API**：檢查是否有「所有錯誤都回 200」的反模式
2. **建立團隊規範**：制定狀態碼使用指南與統一的錯誤格式
3. **更新監控規則**：確保告警規則能正確識別 4xx 與 5xx 錯誤
4. **導入 OpenAPI**：將錯誤回應納入 API 文件，提升團隊溝通效率

記住，好的 API 