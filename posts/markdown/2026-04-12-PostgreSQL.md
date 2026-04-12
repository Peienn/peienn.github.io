# PostgreSQL 連線池調校實戰：用 PgBouncer 解決連線數爆炸問題

## 前言

在生產環境中，你是否曾遇過這樣的錯誤訊息：`FATAL: too many connections for role "app_user"`？隨著應用程式規模擴大，每個 Pod、每個 Worker 都各自維護資料庫連線，PostgreSQL 預設的 `max_connections = 100` 很快就會成為瓶頸。

更麻煩的是，PostgreSQL 對每個連線都會 fork 一個獨立的 backend process，當連線數飆高時，記憶體消耗與 context switch 成本會急遽上升，導致整體效能下降。這時候，連線池（Connection Pooler）就是你的救星。本文將帶你實作 PgBouncer，徹底解決連線數管理的痛點。

## 為什麼不該直接調高 max_connections

許多工程師的第一反應是直接修改 PostgreSQL 設定：

```sql
ALTER SYSTEM SET max_connections = 500;
SELECT pg_reload_conf();
```

這看似簡單，但會帶來嚴重副作用。每個連線約消耗 5-10 MB 記憶體，500 個連線就可能吃掉 5 GB RAM。此外，PostgreSQL 的鎖管理與 snapshot 機制在高連線數下效率會明顯降低。

根據 PostgreSQL 官方建議，實際 `max_connections` 應控制在 CPU 核心數的 2-4 倍以內。以 8 核心主機來說，理想上限約 32-64 個活躍連線。超過這個數字，你需要的不是更多連線，而是連線池。

## PgBouncer 安裝與基本配置

PgBouncer 是最輕量且穩定的 PostgreSQL 連線池解決方案。在 Ubuntu/Debian 上安裝：

```bash
sudo apt update && sudo apt install pgbouncer -y
```

主要設定檔位於 `/etc/pgbouncer/pgbouncer.ini`，以下是生產環境建議配置：

```ini
[databases]
myapp_db = host=127.0.0.1 port=5432 dbname=production_db

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

; 連線池模式：transaction 最常用
pool_mode = transaction

; 每個 user/database 組合的最大連線數
default_pool_size = 25
max_client_conn = 1000
max_db_connections = 50

; 連線生命週期管理
server_idle_timeout = 300
server_lifetime = 3600
```

建立使用者認證檔 `/etc/pgbouncer/userlist.txt`：

```bash
# 從 PostgreSQL 取得密碼 hash
psql -h localhost -U postgres -c "SELECT concat('\"', usename, '\" \"', passwd, '\"') FROM pg_shadow WHERE usename = 'app_user';" >> /etc/pgbouncer/userlist.txt
```

## 三種 Pool Mode 的選擇策略

PgBouncer 提供三種連線池模式，選錯會導致應用程式錯誤：

```ini
pool_mode = session      # 連線完全獨佔，等同沒開連線池
pool_mode = transaction  # 以交易為單位共享連線（推薦）
pool_mode = statement    # 每個 SQL 語句後歸還連線
```

**Transaction mode** 是大多數情況的最佳選擇，但有個重要限制：不能使用 prepared statements 和 session-level 設定。如果你的應用依賴這些功能，需要特別處理：

```python
# Python SQLAlchemy 範例：關閉 prepared statements
engine = create_engine(
    "postgresql://app_user:pass@localhost:6432/myapp_db",
    connect_args={"prepare_threshold": 0}  # 關鍵設定
)
```

## 監控與故障排除

PgBouncer 內建管理介面，連線到管理端口即可查看即時狀態：

```bash
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer

# 查看連線池狀態
pgbouncer=# SHOW POOLS;

# 查看當前活躍連線
pgbouncer=# SHOW CLIENTS;

# 查看後端資料庫連線
pgbouncer=# SHOW SERVERS;
```

關鍵監控指標：
- `cl_waiting`：等待連線的客戶端數量，若持續 > 0 代表連線池太小
- `sv_active`：活躍的後端連線數
- `avg_wait_time`：平均等待時間，超過 100ms 需要關注

整合 Prometheus 監控：

```bash
# 使用 pgbouncer_exporter
docker run -d -p 9127:9127 \
  -e PGBOUNCER_EXPORTER_HOST=pgbouncer-host \
  -e PGBOUNCER_EXPORTER_PORT=6432 \
  prometheuscommunity/pgbouncer-exporter
```

## 結論與行動建議

PgBouncer 是解決 PostgreSQL 連線數問題的標準方案，幾乎零成本就能讓你的資料庫支撐數十倍的客戶端連線。建議你立即執行以下步驟：

1. 檢視目前 `max_connections` 使用率：`SELECT count(*) FROM pg_stat_activity;`
2. 在 staging 環境部署 PgBouncer，選用 transaction mode
3. 設定監控告警，當 `cl_waiting` 持續大於 0 時發出通知
4. 進行壓力測試，確認應用程式與 PgBouncer 的相容性

別等到連線爆炸才處理，現在就把 PgBouncer 加入你的基礎架構吧！

---
date: 2026-04-12
topic: PostgreSQL
tags: [devops, postgresql, pgbouncer, connection-pool, database, performance-tuning]
---