上一篇文章提到，在多人聊天室架構中加入 Nginx，雖然能實現反向代理及流量控制，  
但也導致使用者被隨機分配到不同的聊天室實例，無法保證在同一間聊天室中互動。

![123](noredis.png)

這個問題可以透過 Redis 的 **Pub/Sub** 功能來解決


# 主要流程
1. Redis 介紹
2. Redis 安裝
3. 測試


# Redis 介紹

Redis 是一種 **NoSQL 資料庫（鍵值 key-value store）**。資料主要存放於 **記憶體 (RAM)** 中，讀寫速度極快，因此以高速的記憶體存取為特色。  

## 核心特性
- **多種資料類型**：除了基本的字串 (String)，還支援清單(List)、集合(Set)、雜湊(Hash)、有序集合(Sorted Set) 等，方便處理各種不同需求。
- **原子操作**：Redis 的指令操作一次完成，不會被其他操作打斷，確保資料一致性。
- **容易擴展**：支援主從複製、資料分片（Sharding），還有集群(Cluster)架構，可以隨系統需求增加機器，提升效能與可用性。
- **輕量部署**：單一執行檔，安裝快速，資源消耗低。


## 持久化機制 

Redis 既然是存放在記憶體內，如何持久化（資料永久保存）以確保資料在斷電或重啟後可恢復 ?

1. **RDB (Snapshotting)**  
   - 以指定的時間間隔，將記憶體裡的資料快照存成二進位檔 `.rdb`。重啟時會載入這些快照還原資料。  
   - 優點：備份檔案小，恢復速度快，但資料更新非即時。*

2. **AOF (Append Only File)**  
   - 將每筆寫入命令依序追加至日誌檔案，重啟時依序執行命令進行資料還原。  
   - 優點：資料持久化更即時，可減少資料遺失風險，但檔案較大且恢復速度較慢。*

3. **兩者可同時啟用**，兼顧資料安全與恢復效率。


## Redis 常見應用場景
- **快取 (Caching)**  
  快速緩存熱門資料，減輕後端資料庫壓力，提升系統效能。

- **會話管理 (Session Management)**  
  集中管理使用者登入狀態與資訊，支援多台伺服器共享 session。

- **排行榜 (Leaderboards)**  
  利用 **Sorted Set** 快速計算和更新排名。

- **訊息佇列與發布/訂閱 (Message Queue & Pub/Sub)**  
  實現即時通知與跨服務訊息傳遞。

- **即時數據分析**  
  支援高頻率讀寫的即時統計與監控系統。

---



# Redis 安裝
下面以常見的作業系統為例，說明如何安裝 Redis。<br>
(Redis 官方沒有正式 Windows 版本)


## 1. 在 Ubuntu / Debian Linux 安裝

```markdown
# 更新套件清單
sudo apt update 

# 安裝 Redis 伺服器
sudo apt install redis-server

# 啟動 Redis 服務
sudo systemctl start redis

# 設定開機自動啟動
sudo systemctl enable redis

# 檢查 Redis 是否正常運作。若回傳 PONG 表示運作正常
redis-cli ping
```
## 2. 在 macOS 安裝 (使用 Homebrew)
```markdown
# 安裝 Redis
brew install redis

# 啟動 Redis
brew services start redis

# 測試 Redis 是否正常
redis-cli ping
```
---

# 測試

![redis](redis.png)
