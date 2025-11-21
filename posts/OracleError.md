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

---

# ORA-01653: unable to extend table

通常是Table 無法在 Tablespace 中取得足夠的空間來擴充資料。這與 Tablespace 的空間配置設計關，兩種主要解決方式和優缺點分析。

---


| 配置方式           | 優點                                                         | 缺點                                                       | 適用場景                          |
|--------------------|--------------------------------------------------------------|------------------------------------------------------------|-----------------------------------|
| **1. Tablespace Autoextend** | - 動態擴充，彈性大，可因需求自動增加空間<br>- 減少空間不足導致錯誤的發生<br>- 管理較靈活 | - 未設定最大值時可能無限制膨脹，導致整個磁碟耗盡<br>- 多次小幅擴充可能導致`資料檔碎片`<br>- 需有良好監控避免空間耗盡 | 需求波動大、難以準確估計容量的測試環境或開發環境<br>資料量成長不易預測的系統 |
| **2. 固定大小預先配置** | - 空間利用集中，減少碎片且效能穩定<br>- 空間分配容易掌控和監管<br>- 減少因突發空間擴充導致的問題 | - 若容量預估不足，可能導致空間不足錯誤如ORA-01653<br>- 須人工監視與擴充，可能需停機操作<br>- 初期預留空間可能造成`資源浪費` | 生產環境中容量相對穩定且需穩定效能<br>資源管理與監控嚴格的系統 |

---

綜合建議

- **生產環境**：  
  可先(2)以固定大小預配置，再設定適當的(1) `autoextend` 且限定最大大小，兼顧穩定與彈性。

- **監控必須**：  
  無論使用哪種方式，都要建立空間使用監控與警示，避免突發空間不足。

- **碎片管理**：  
  使用 autoextend 應注意資料檔碎片的問題，定期重組(re-build)資料表與索引。

---
