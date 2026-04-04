# RESTful API 設計：如何優雅處理版本控制策略

## 前言

在微服務架構盛行的今天，API 版本控制是每位後端工程師都會遇到的挑戰。當你的 API 需要進行破壞性變更，卻有數十個內部服務與外部客戶仍在使用舊版本時，該如何平穩過渡？選錯版本控制策略，輕則造成團隊溝通成本上升，重則導致線上服務中斷。本文將深入探討三種主流的 API 版本控制方式，並提供實務上的選擇建議。

## URL Path 版本控制：直覺但有代價

最常見的做法是將版本號直接放在 URL 路徑中：

```
GET /api/v1/users/123
GET /api/v2/users/123
```

這種方式的優點是極度直覺，開發者一眼就能辨識 API 版本。在 Nginx 配置中，你可以輕鬆將不同版本路由到不同後端：

```nginx
location /api/v1/ {
    proxy_pass http://api-v1-service:8080/;
}

location /api/v2/ {
    proxy_pass http://api-v2-service:8080/;
}
```

然而，這種方式違反了 REST 的核心原則——URI 應該代表資源本身，而非資源的表現形式。當你有 50 個 endpoint 需要升版時，就會產生大量重複的路由配置。GitHub 早期採用此方案，但後來也逐漸轉向其他策略。

## Header 版本控制：符合 REST 精神的選擇

透過自訂 Header 傳遞版本資訊是更符合 REST 設計理念的做法：

```bash
curl -H "X-API-Version: 2" https://api.example.com/users/123

# 或使用 Accept Header
curl -H "Accept: application/vnd.example.v2+json" https://api.example.com/users/123
```

在 Spring Boot 中，你可以這樣實作版本判斷：

```java
@GetMapping(value = "/users/{id}", headers = "X-API-Version=2")
public ResponseEntity<UserV2> getUserV2(@PathVariable Long id) {
    return ResponseEntity.ok(userService.getUserV2(id));
}
```

這種方式保持了 URI 的純淨，但增加了客戶端的使用複雜度。測試時無法直接在瀏覽器輸入 URL，必須依賴 Postman 或 curl 等工具。Stripe 和 Microsoft Azure 部分服務採用此策略。

## Query Parameter 版本控制：折衷的務實方案

將版本號作為查詢參數是一種折衷方案：

```
GET /api/users/123?version=2
```

這種方式易於實作，且可以設定預設版本：

```python
# FastAPI 範例
@app.get("/users/{user_id}")
async def get_user(user_id: int, version: int = 1):
    if version == 2:
        return await get_user_v2(user_id)
    return await get_user_v1(user_id)
```

但 Query Parameter 通常用於過濾和排序，用來傳遞版本資訊在語義上稍顯混淆。此外，快取機制需要額外注意將版本參數納入 cache key。

## 實務建議：混合策略與 API Gateway 整合

在真實的生產環境中，我建議採用混合策略搭配 API Gateway：

```yaml
# Kong API Gateway 配置範例
services:
  - name: user-service
    url: http://user-service:8080
    routes:
      - name: users-v1
        paths:
          - /api/v1/users
        strip_path: true
      - name: users-v2
        paths:
          - /api/v2/users
        headers:
          X-API-Version:
            - "2"
```

主版本變更（如 v1 到 v2）使用 URL Path，次要變更則透過 Header 控制。同時，務必在 Response 中加入版本棄用警告：

```json
{
  "data": { ... },
  "meta": {
    "api_version": "1",
    "deprecation_warning": "v1 將於 2025-06-01 停止支援"
  }
}
```

## 結論

API 版本控制沒有銀彈，選擇取決於團隊規模、客戶類型與維運能力。對於多數中型團隊，我推薦 URL Path 作為主版本控制（易於理解與部署），搭配 Header 處理細微變化。最重要的是，無論選擇哪種策略，都要建立明確的棄用政策與通知機制，讓 API 消費者有充足時間進行遷移。

---
date: 2026-04-04
topic: RESTful API 設計
tags: [devops, api-design, versioning, api-gateway, backend]
---