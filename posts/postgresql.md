關聯式資料庫管理系統 (RDBMS)有很多選擇:
 - Open : MySQL, PostgreSQL
 - Business : Oracle, Microsoft SQL Server 

因為是個人專案所以從開源中選擇，挑選PostgreSQL原因 :

-  **功能比較強大**  
   PostgreSQL 支援更多元的功能和資料類型，能處理更複雜的資料和需求。

-  **穩定可靠，資料安全**  
   它對資料一致性和安全性要求很高，適合重要資料的存放。

-  **有一定領域知識**  
   目前工作內容中一部分是負責公司 OracleDB 的維運管理

| 項目       | PostgreSQL               | MySQL                     |
|------------|-------------------------|---------------------------|
| 功能       | 多功能、支援進階資料類型    | 功能基本，較適合簡單應用       |
| 資料安全   | 嚴格符合 ACID 標準         | 部分儲存引擎支援 ACID        |
| 效能       | 高頻寫入效能               | 高頻讀取效能                 |
| 索引類型   | 支援多種索引               | 支援基本索引                 |
| 上手難易度 | 較複雜                   | 較容易                      |



# 主要流程

1. PostgreSQL 介紹
2. PostgreSQL 安裝
    - 安裝方式
    - 資料庫備份
    - 異常偵測
3. PostgreSQL 實作 (搭配聊天室)




## 1. PostgreSQL 介紹

PostgreSQL 是一個功能強大且開源的 RDBMS ，具備高度擴展性與可靠性。它支援標準 SQL 語法，並且提供豐富的資料型別、複雜查詢、事務處理與多版本併發控制（MVCC），適合構建企業級應用與網路服務。








## 2. PostgreSQL 安裝

### 安裝方式

1. Windows

2. Ubuntu Linux 


### 資料庫備份

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

- **pgAudit** 是 PostgreSQL 官方推薦的審計套件，可以詳細記錄資料庫內的 DDL、DML 操作以及角色權限變動。


   1. 安裝 pgAudit， 修改 postgresql.conf 加入： shared_preload_libraries = 'pgaudit'，重新啟動 PostgreSQL。

   2. ALTER SYSTEM SET pgaudit.log = 'role, ddl';

      #### `role` 類別 : 與角色（Roles）及權限相關的所有操作，包括：
      - 建立角色（`CREATE ROLE`、`CREATE USER`）  
      - 刪除角色（`DROP ROLE`、`DROP USER`）  
      - 權限指派（`GRANT`）與收回（`REVOKE`）  
      - 修改角色屬性（如密碼、登入權限變更）  

      #### `ddl` 類別 : 資料定義語言（DDL）類操作，包含對資料庫結構的更動，如：
      - 建立／刪除／修改資料表（`CREATE TABLE`, `DROP TABLE`, `ALTER TABLE`）
      - 建立／刪除／修改索引（`CREATE INDEX`, `DROP INDEX`）  
      - 建立／刪除／修改視圖、序列、函式等物件  


   3. SELECT pg_reload_conf();  //重新載入設定檔

