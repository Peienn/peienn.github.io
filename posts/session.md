
上一篇提到缺少`會話管理機制`，導致使用者每次進入聊天室時，都必須重新輸入名稱，無法記住之前的狀態。

這是因為系統沒有儲存使用者的會話資訊，無法識別「這個使用者之前訪問過」。

為了解決上述問題，這次將加入 **Session** 。

<br>
<br>


# 主要流程

1. Session 與 Cookie 介紹
2. Redis Session Store 介紹
3. Session 實作

## 1. Session 與 Cookie 介紹



- Session 是常見的伺服器端會話管理機制，用來記錄並維護使用者登入狀態。當使用者輸入正確的帳號/密碼後，伺服器會產生一組唯一的 Session，並將其資料儲存於資料庫或快取系統（如 Redis）中。

    - Session 內有一組唯一識別碼 : Session ID
    - Session 可以設定時效性
    - 管理方便，可以直接至資料庫刪除Session



-  Cookie 是瀏覽器用來儲存少量資料的機制，可以想像成`瀏覽器自帶的一個小型文字檔`。<br>當`開發者希望瀏覽器在之後的請求中帶上某些認證或辨識資訊`時，會在後端的 HTTP 回應中加入 Set-Cookie 標頭，告訴瀏覽器要建立或更新 Cookie。<br>`瀏覽器收到這個HTTP 回應後，會將資訊儲存在 Cookie 中`，並在未來對同一個網站的請求，自動夾帶這些 Cookie，協助後端辨識使用者身分或狀態。

    - 主要用於維持會話狀態、存放識別碼、個人化偏好設定
    - 每次請求都會攜帶，應避免放太大或敏感資料。


![123](cookie.png)


---


Redis Session Store 介紹




---

安裝套件介紹

- express-session : Node.js用於建立和管理Session。
- connect-redis : 專門為express session設計的 `保存Session機制`





1. express-session 負責管理 Session 的整個生命週期與操作邏輯（例如建立 Session、更新內容、過期時間管理、刪除 Session 等）。但它本身不直接知道如何把 Session 資料「存到具體的地方」。它只定義一套操作 Session 的抽象介面（Session Store interface）。

2. Redis 本身是一個 Key-Value 資料庫，它「不懂」什麼是 Session，也不會自動處理 Session 特殊的生命週期動作。


connect-redis 就是這個「橋樑」或「轉譯器」，實作 express-session 的 Session Store 介面。告訴 express-session 怎麼用 Redis 命令來存、讀、更新和刪除 Session，讓 Redis 能「配合」express-session 管理 Session。


所以是 express-sesison 產生 session , 並且 express-session會利用connect-redis， 而connect-redis在利用redisclient 操作 Redis Server

最終形成 express-session可以操作Redis server
