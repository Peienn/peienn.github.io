# 相關文章
<a href="https://peienn.github.io/posts/templates.html?file=posts/index.md" class="custom-link">資料庫 Index 介紹 </a>

<style>
.custom-link {
  display: inline-block;
  width: 50%;
  padding: 10px 15px;
  background-color: rgba(255, 99, 71, 0.15);  /* 透明珊瑚橘 */
  color: #FF6347;
  text-align: center;
  text-decoration: none;
  border: 2px solid rgba(255, 99, 71, 0.5);
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  backdrop-filter: blur(6px);
  transition: all 0.3s ease;
}

.custom-link:hover, 
.custom-link:focus {
  background-color: rgba(255, 99, 71, 0.35);
  border-color: #FF6347;
  color: #CC4A38;
  cursor: pointer;
  box-shadow: 0 8px 16px rgba(255, 99, 71, 0.3);
}
</style>



# 主要流程

1. PostgreSQL 介紹
2. PostgreSQL 安裝
    - 安裝方式
    - 資料庫備份
    - 異常偵測
3. PostgreSQL 實作 (搭配聊天室)




## 1. PostgreSQL 介紹

介紹PostgreSQL之前，先討論市占率最高的 關聯式資料庫管理系統 (RDBMS) :

 - 開源 (Open) : MySQL, PostgreSQL
 - 商用 (Business) : Oracle, Microsoft SQL Server 

因為是個人專案所以從`開源`中選擇，而挑選 `PostgreSQL`原因 :

-  **功能比較強大**  
   PostgreSQL 支援更多元的功能和資料類型，能處理更複雜的資料和需求。

-  **穩定可靠，資料安全**  
   它對資料一致性和安全性要求很高，適合重要資料的存放。

-  **具備領域知識**  
   目前工作內容中一部分是負責公司 OracleDB 的維運管理

| 項目       | PostgreSQL               | MySQL                     |
|------------|-------------------------|---------------------------|
| 功能       | 多功能、支援進階資料類型    | 功能基本，較適合簡單應用       |
| 資料安全   | 嚴格符合 ACID 標準         | 部分儲存引擎支援 ACID        |
| 效能       | 高頻寫入效能               | 高頻讀取效能                 |
| 索引類型   | 支援多種索引               | 支援基本索引                 |
| 上手難易度 | 較複雜                   | 較容易                      |


由此可知，PostgreSQL 是一個兼具穩定性、彈性與專業級能力的資料庫系統。



## 2. PostgreSQL 安裝

### 安裝方式

#### 1. Windows

```bash
其實就是去官網下載，然後執行這樣。
Port : 5432 (Default)
輸入的密碼要記得。 (但忘記也可以找回)
```

![123](images/postgresql/windows_download.png)

#### 2. Ubuntu Linux 

```bash
# 更新套件
sudo apt update
sudo apt upgrade -y

# 安裝
sudo apt install postgresql postgresql-contrib -y

#  啟動與查看
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

安裝完資料庫，緊接著就是需要針對資料庫進行備份和監控。

### 資料庫備份

**備份重要、很重要、非常重要**。因為不論是 <u>被駭客入侵</u> 或是 <u>操作錯誤</u> 都可以透過完整備份檔將資料恢復。

備份方法有二種 : 邏輯備份和物理備份

- 邏輯備份（Logical Backup）  
  - 匯出 SQL 指令或自訂格式備份。  
  - 適用單一資料庫、小型或中型專案。  
  - 工具：`pg_dump`（單一資料庫備份）、`pg_dumpall`（全部資料庫及使用者備份）。

  ```bash
  # 備份單一資料庫
  pg_dump -U postgres your_database > backup.sql

  # 備份全部資料庫及使用者設定 (不用指定database)
  pg_dumpall -U postgres > all_backup.sql
  ```



- 物理備份（Physical Backup） 
  - 複製整個資料目錄和 WAL 日誌。  
  - 適用大型資料庫、需快速還原環境。  
  - 工具：`pg_basebackup` 搭配 WAL 持續備份。
  ```bash　
  # postgresql.conf 設定範例（需重啟生效）
  wal_level = replica                   # 啟用複寫及進階備份功能
  archive_mode = on                     # 開啟 WAL 歸檔功能
  archive_command = 'cp %p /wal_archive/%f'  # 備份 WAL 檔案到指定目錄

  # 每周 pg_basebackup
  pg_basebackup -h localhost -D /path/to/backup -U replicator -Fp -Xs -P
  
  # replicator 角色需要有 replication 權限
  # 定期清除 WAL 檔案
  ```



### 異常偵測 : pgAudit

這邊主要是針對資料庫的<u>操作異常</u>、<u>影響資料庫安全問題的行為</u> 進行偵測。


- **pgAudit** 是 PostgreSQL 官方推薦的審計套件，可以詳細記錄資料庫內的 DDL、DML 操作以及角色權限變動。

   1. 安裝 pgAudit
   
   2. 修改 postgresql.conf ： 加入 `shared_preload_libraries = 'pgaudit'`，
   
   3. 重新啟動 PostgreSQL。

   4. 開啟audit 功能 `ALTER SYSTEM SET pgaudit.log = 'role, ddl';`

      #### `role` 類別 : 與角色（Roles）及權限相關的所有操作，包括：
      - 建立角色（`CREATE ROLE`、`CREATE USER`）  
      - 刪除角色（`DROP ROLE`、`DROP USER`）  
      - 權限指派（`GRANT`）與收回（`REVOKE`）  
      - 修改角色屬性（如密碼、登入權限變更）  

      #### `ddl` 類別 : 資料定義語言（DDL）類操作，包含對資料庫結構的更動，如：
      - 建立／刪除／修改資料表（`CREATE TABLE`, `DROP TABLE`, `ALTER TABLE`）
      - 建立／刪除／修改索引（`CREATE INDEX`, `DROP INDEX`）  
      - 建立／刪除／修改視圖、序列、函式等物件  

   5.  `SELECT pg_reload_conf();`  //重新載入設定檔



## 3. PostgreSQL 實作 (搭配聊天室)

上一篇 Session 文章中，我們討論的延伸問題是因為目前Redis 是記憶體型資料庫，<u>無法支撐大量訊息作為儲存</u>，以及Key-Value的儲存結構下，<u>無法支撐複雜查詢和資料分析</u>。
也<u>沒有完整的管理功能來保護使用者</u>。因此需要一個 RDBMS 作為後端的主要資料庫。

加入PostgreSQL後要達成的目標 : 

```
📊 資料分層策略
├─ 快速載入（Redis）
│  └─ 最新 50 條訊息
│  └─ Session 資料
│
└─ 永久保存（PostgreSQL）
   └─ 完整聊天記錄
   └─ 使用者資料
   └─ 登入日誌
```


1. **載入最近訊息** → 從 Redis 快速讀取
2. **查詢歷史記錄** → 從 PostgreSQL 撈取
3. **發送新訊息** → 同時寫入 Redis 和 PostgreSQL


### 程式碼和參數調整


這次調整了整個後端的架構，以往都是直接把所有程式碼都寫在 Server.js 內(主程式)，但隨著使用的技術越來越多，如果仍舊把所有Code都寫在一起，就會變得很混亂。
因此這次將架構分離，類似MVC。

- config : 設定檔或連線資訊
- db : 資料庫連線 (Redis, PostgreSQL)
- models : 資料操控
- routes : API 設定
- sockets :　socket連線設定
  
讓 Server.js (主程式) 內更清晰，讓維護者可以快速了解整個後端的架構。

#### 後端

1. 以往都只將訊息寫入Redis。 現在同時也要寫一份到PostgreSQL。
2. 建立獲取PostgreSQL 訊息的API， 讓前端可以在 "觸發條件" 觸發時獲取歷史訊息。

#### 前端

1. 以往輸入名稱按下加入後會直接進入，現在按下加入會去call API /login , 檢查名稱是否存在PostgreSQL，如果不存在的話就拒絕進入
2. 新增"註冊"按鈕，當按下按鈕後，會call API /register，檢查名稱是否存在資料庫，如果不存在的話就會寫入資料庫並允許進入，否則回傳錯誤 "已註冊"。
3. 聊天室內加入 "載入更多歷史訊息"按鈕， 按下後會call API /history , 後端會回傳訊息。前端在將訊息插入到目前的聊天室。 

<br>

其實加入PostgreSQL後，只不過是在過往的基礎上，多了一些判斷和行為而已。



### 實際結果

1. 首先，確認資料庫是乾淨的。

![123](images/postgresql/init_db.png)


2. 打開網站，輸入任意的名稱。 但會發現你進不去，因為要登記在資料庫的名稱才有權限可以進入。

![123](images/postgresql/Login_non-authorization.png)


3. 透過註冊，後端將名稱寫入資料庫，才允許該名稱進入聊天室。同時開始寫入Redis 和 PostgreSQL ("名稱" 已加入聊天室) <br>
   (這邊用兩個名稱 "amber" 與 "brent" 做後續測試)

![123](images/postgresql/register.png)



中間在做任何事的時候，都可以直接到redis檢查。
例如，初始化時聊天室的長度是0 ; 用 Set 紀錄線上使用者的數量也是 0

直到 "amber" 和 "brent" 註冊完也輸入完訊息後，再次檢查就會看到redis發生變動。

![123](images/postgresql/redis.jpg)



4. 這時候，我們到PostgreSQL查看 users表，會看到剛剛註冊的 "amber" , "brent" , 以及用來記錄系統資訊的 "system"

![123](images/postgresql/register_db.png)


5. 成功進入聊天室後，開始寫訊息，中間測試 "brent" `登出`會呈現甚麼狀況。 <br>

   可以看到系統會顯示 "brent"已離開聊天室給所有聊天室成員看。

![123](images/postgresql/logout.png)

6. 當 "brent" 輸入名稱重新回來之後，滑到最上面會看到呈現的訊息與 "amber" 不同。  <br>
   因為每次進入聊天室的人，獲取到的訊息都是從Redis來的 (快速)，而Redis目前設定只保存 50筆 訊息。 <br>
   這時可以讓我們測試 `載入歷史訊息` 的功能是否正常。

![123](images/postgresql/loginWithSession.png)


7. 結合上圖可以發現，訊息有正確的被載入 4 的前面是 3 2 1 而且都由 "amber"輸入。(輸入訊息時是從1~50) <br>
   包含最初近來聊天室系統所發出的 "已加入聊天室"。

![123](images/postgresql/loadHistory.png)


8. 最後，讓兩位使用者都離開聊天室。並進到PostgreSQL 查看訊息。

![123](images/postgresql/message_db.png)

---


# 結論


現在，我們使用了 3 個後端會用到的技術建立了一個簡單的聊天室。

- Nginx : 流量控制 + 反向代理
- Redis : Session 管理 + 多伺服器資訊共享 (Pub/Sub)
- PostgreSQL :　訊息永久保存



![architecture](images/postgresql/architecture.png)



接下來，將進入到偏向維運的部分，讓系統`更穩定、易管理`。

- Docker Compose : 服務容器化與統一管理
- Grafana + Prometheus : 效能監控
- ELK : :LogFile 分析平台


