# ORA-12519, TNS:no appropriate service handler found

Process過多會導致 Oracle listener收到請求時找不到service handler可以處理

1跟sesison通常對應一個process，如果其中一個滿了就會導致client無法連線至db

所以要先檢查 process , session的最大值以及當前使用量


```markdown
#目前多少process
SELECT COUNT(*) FROM V$PROCESS;
#系統設定Process最大值
SHOW PARAMETER processes;


#檢查Session
SELECT 
    STATUS,
    COUNT(*) AS SESSION_COUNT
FROM V$SESSION 
WHERE STATUS IN ('ACTIVE', 'INACTIVE')
GROUP BY STATUS;
#系統設定Session最大值
SHOW PARAMETER sessions;
```

此次案例為:

Session 最大值700
- Session Active : 23
- Session Inactive : 413 <br>

Process 系統最大值450 
- Process 目前 442

可以看出是因為Prcoess已經接近最大值 + 大部分的Session都是Inactive導致。

---

Q:為甚麼有那麼多Inactive ? 

先輸入指令找出這些Inactive Session的資訊，從Event中找到都是 : SQL*Net message from client
```markdown
# 找出INACTIVE Sesson的資訊
SELECT
    s.sid,
    s.serial#,
    s.username,
    s.status,
    s.event,
    s.machine,
    s.program,
    s.module,
    s.client_info,
    s.logon_time,
    s.last_call_et,          -- 到目前閒置多久（秒）
    p.spid,                  -- OS process id
    p.pid,                   -- Oracle process id
    p.background             -- 是否為背景進程，0=用戶，1=背景
FROM
    v$session s
    JOIN v$process p ON s.paddr = p.addr
WHERE
    s.status = 'INACTIVE'
ORDER BY
    s.last_call_et DESC;
```



SQL*Net message to client 是什麼？
- 這個等待事件代表 Oracle 伺服器正在 向客戶端傳送資料（例如查詢結果、訊息等），但因某些原因等待完成這個動作。
- 換句話說，資料庫伺服器已經完成處理，準備將資料發送給客戶端，但因為傳輸上受阻（客戶端忙碌、網路延遲、頻寬或硬體問題等）造成傳送有等待。

主要可能原因
- 客戶端無法及時接收 : 客戶端可能在忙碌（例如UI畫面沒更新或暫時不讀取資料），導致伺服器的送出訊息被阻塞。
- 網路問題 : 網路延遲或封包丟失，導致通訊不順利，伺服器必須等待傳輸完成。


可解決方案 : 

1. kill session
2. $ORACLE_HOME/network/admin/sqlnet.ora  (SQLNET.EXPIRE_TIME = 10)
