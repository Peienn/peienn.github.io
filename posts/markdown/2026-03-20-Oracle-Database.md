# Oracle Database AWR 報告實戰：快速診斷效能瓶頸的關鍵技巧

## 前言

當 Oracle Database 出現效能問題時，DBA 和 DevOps 工程師最常面臨的挑戰就是：「到底是哪裡慢？」在沒有完整監控體系的情況下，AWR（Automatic Workload Repository）報告是 Oracle 內建最強大的效能診斷工具。然而，一份 AWR 報告動輒數百頁，許多工程師拿到報告後往往不知從何下手。

本文將聚焦於 AWR 報告中最關鍵的幾個區塊，教你如何在 10 分鐘內定位 80% 的效能問題，讓你在處理線上緊急狀況時能夠快速反應。

## 產生 AWR 報告的正確方式

在開始分析之前，首先要確保你能正確產生 AWR 報告。以 sysdba 身份登入後，執行以下指令：

```sql
-- 查看可用的 snapshot 範圍
SELECT snap_id, begin_interval_time, end_interval_time 
FROM dba_hist_snapshot 
WHERE begin_interval_time > SYSDATE - 1
ORDER BY snap_id;

-- 產生 HTML 格式的 AWR 報告
@$ORACLE_HOME/rdbms/admin/awrrpt.sql
```

執行後系統會詢問報告格式（建議選 html）、資料庫 ID、以及起始與結束的 snapshot ID。關鍵技巧是：**選擇問題發生的時間區間**，通常 30 分鐘到 2 小時的區間最能反映問題。若選擇太長的時間範圍，數據會被平均化而失去診斷價值。

## 第一站：DB Time 與 Load Profile

打開 AWR 報告後，第一個要看的是「Load Profile」區塊。這裡有幾個關鍵指標：

```
指標名稱              每秒數值    每次交易數值
--------------------------------------------------------
DB Time(s):           45.2        0.8
DB CPU(s):            12.1        0.2
Redo size (bytes):    2,847,293   52,184
Logical reads:        892,471     16,348
Physical reads:       23,847      437
```

**DB Time** 是最重要的指標，代表資料庫實際花費的時間。如果你的伺服器有 8 顆 CPU，理論上每秒最大 DB Time 是 8 秒。當 DB Time 遠超過 CPU 數量時，代表有大量等待事件發生。

計算公式：`DB Time = DB CPU + Wait Time`

若 DB CPU 佔 DB Time 的比例很低（如上例只有 27%），代表系統大部分時間都在等待，需要進一步查看等待事件。

## 第二站：Top 5 Timed Events 找出真兇

這是整份報告最關鍵的區塊，直接告訴你資料庫把時間花在哪裡：

```
Event                          Waits      Time(s)  Avg wait(ms)  % DB time
---------------------------------------------------------------------------
db file sequential read        847,293    1,892    2.23          42.1
DB CPU                                    1,210                   26.9
log file sync                  234,847    847      3.61          18.8
db file scattered read         123,456    312      2.53          6.9
library cache lock             8,234      198      24.05         4.4
```

常見等待事件的診斷方向：

- **db file sequential read**：單區塊讀取，通常是索引掃描。過高代表可能缺少索引或索引效率差
- **db file scattered read**：多區塊讀取，通常是全表掃描。檢查是否有遺漏索引或統計資訊過期
- **log file sync**：Redo log 寫入等待。檢查儲存 I/O 效能或考慮調整 commit 頻率
- **library cache lock**：SQL 解析相關。可能是硬解析過多，檢查是否使用綁定變數

## 第三站：SQL Statistics 揪出問題 SQL

定位到等待事件後，下一步是找出造成問題的具體 SQL。AWR 報告提供多種排序方式：

```
SQL ordered by Elapsed Time
SQL ordered by CPU Time  
SQL ordered by Gets（邏輯讀取）
SQL ordered by Reads（物理讀取）
SQL ordered by Executions
```

建議優先查看「SQL ordered by Elapsed Time」，找出執行時間最長的 SQL。報告會顯示 SQL ID，你可以用以下指令取得完整 SQL 文字與執行計畫：

```sql
-- 查看完整 SQL 文字
SELECT sql_fulltext FROM v$sql WHERE sql_id = 'abc123xyz';

-- 從 AWR 取得歷史執行計畫
SELECT * FROM TABLE(DBMS_XPLAN.display_awr('abc123xyz'));
```

拿到執行計畫後，重點檢查是否有全表掃描（TABLE ACCESS FULL）、笛卡爾積（MERGE JOIN CARTESIAN）、或估算行數與實際行數差異過大的情況。

## 結論與行動建議

AWR 報告診斷的核心流程可以簡化為：**Load Profile 看整體健康 → Top Events 找等待原因 → SQL Statistics 定位問題 SQL → 執行計畫分析根因**。

給中階 DevOps 工程師的具體建議：

1. **建立基準線**：在系統正常時產生 AWR 報告作為 baseline，異常時才有比較依據
2. **自動化收集**：使用 `DBMS_WORKLOAD_REPOSITORY.create_snapshot` 在關鍵時間點手動建立快照
3. **搭配 ASH**：對於短暫的效能問題，ASH（Active Session History）報告能提供更細緻的秒級分析
4. **整合監控**：將關鍵指標（如 DB Time、Top Wait Events）整合到 Prometheus + Grafana，實現即時告警

掌握 AWR 報告分析技巧，能讓你在效能問題發生時快速縮小排查範圍，從「盲目猜測」轉變為「數據驅動」的問題解決模式。

---
date: 2026-03-20
topic: Oracle Database
tags: [devops, oracle, awr, performance-tuning, database, monitoring]
---