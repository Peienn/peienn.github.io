
# Oracle Server 資料庫


## 設計架構

Oracle 資料庫主要由兩個部分組成，資料庫(Databae) +  執行處理(Instance)

- Database 是一堆實體檔案，負責保存資料
- Instance 是一堆程式，負責處理資料

### Database

有兩種結構，實體結構 (Physical Structure) 和邏輯結構 (Logical Structure)。

1. 實體結構 : 真實存放在 Disk 的檔案，例如: Controlfile, DataFile 等。
    - Controlfile : 存放資料庫相關的重要資訊，如資料庫的實體結構位置，若是遺失恐導致 Instance 找不到 Datafile，進而影響資料庫無法開啟。最少 1 個，最多 8 個，且每個都要相同。
    - DataFile : 實際存放資料 (Data)，不論是Table、Index 還是資料字典都會放在DataFile內。
    - Online Redo Logfile : 當災難發生時用來還原資料庫的交易。資料庫正常運行下此檔案毫無作用。

2. 邏輯結構 : 記錄資料庫邏輯物件的定義與關聯，是一種抽象結構。主要目的是為了讓資料庫的空間更有效率的使用 [[1]](#1)<a id="b1"> </a>。例如: Tablespace, Segment, Block。<br>
   就好像用windows時，你只知道 C:\Documents\報告.docx (邏輯結構)，但檔案實際上可能分散存在硬碟的不同磁區 (物理結構)。


### Instance 

由兩大部分組成 : System Global Area(SGA) + Background Processes

- SGA : 多種不同的共用記憶體元件組合的區塊，但下列三種是必要的:
    - Shared Pool : 有很多區塊組合且各自有功能。例如其中的 Result Cache 負責記錄先前SQL獲取的結果，下次如果執行相同SQL，會直接到Result Cache獲取結果，就不需要往下處理。
    - Buffer Cache : 所有的實際資料都要先載入到此，才能進行讀寫。
    - Log Buffer : 用來記錄每一筆 SQL 的 Redo Entry，是為了當災難發生時可以進行 Instance Recovery[[2]](#2)<a id="b2"> </a>。

- Background Processes : 負責資料庫的各種處理，下列五種是必要的:

    - SMON (System Monitor): Oracle資料庫開機時，檢查資料庫上次的關機是不是正常，若不是的話會開啟 Instance Recovery  。
    - PMON (Process Monitor): 監控其他的 Process，例如當 PMON 發送訊息給User Process很久都沒回應，PMON會判定該Process 已死，退回它的交易並且釋放它的資源。
    - DBWR (Database Writer): 將 Buffer Cache內的  Dirty Cache [[3]](#3) <a id="b3"> </a>寫回 DataFile
    - LGWR (Log Writer): 將 Log Buffer內的 Redo Entry 寫到線上重做日誌檔 (Online Redo Logfile)
    - CKPT (Checkpoint): 當發生檢查點事件，CKPT 會要求 DBWR將Dirty Cache寫回DataFile，並將檢查點資訊寫到 ControlFile 和 Datafile Header 。同時，每3秒會將重做位元組位置 (Redo Byte Address) 寫到 ControlFile中，當進行 Instance Recovery時可以依據 Redo Byte Address 去 Online Redo Logfile 找出 Redo Entry，並用以復原檔案。

![oracle server 架構圖](../images/oracle/arch.png)


### 運作流程

當今天一個使用者在SQL中下了 SELECT ，資料庫會怎麼做

![oracle server 架構圖](../images/oracle/select.png)

#### 流程說明 :

1. 當使用者下了 SELECT後，透過 User Process 傳遞至 Oracle Server 
2. Oracle Serve Prcoess 接收後會到 Buffer Cache檢查這一筆資料在哪一個資料區塊中
    - 如果找到了 : 直接回傳對應的 Rows
    - 如果找不到 : 到 Datafile 實體檔案中找出該資料區塊，並將其讀入buffer Cache。<br>這是一個 I/O operations，自然會比直接在buffer cache找到後直接回傳還要慢 (Cache operations)。


#### 注意:

如果 buffer cache 沒有空間可以讓Server Process 可以將資料從datafile移至 ，怎麼辦?

Server Process 會到LRU串列尋找可使用緩衝，中間如果遇到dirty buffer ，會將其移動Checkpoint Queue，如果因此導致checkpoint Queue滿了，
Server Process 暫停搜尋並且要求DBWR將checkpoint queue內的dirty buffer 寫回datafile，結束後 Server Process 繼續去LRU 串列搜尋可用緩衝。

---

當今天一個使用者在SQL中下了 UPDATE/INSERT/DELETE ，資料庫會怎麼做

!
![oracle server 架構圖](../images/oracle/update.png)


#### 流程說明 :

1. 當使用者下了 SELECT後，透過 User Process 傳遞至 Oracle Server 
2. Oracle Serve Prcoess 接收後會到 Buffer Cache檢查這一筆資料在哪一個資料區塊中，如果找不到就到 Datafile 實體檔案中找出該資料區塊，並將其讀入buffer Cache。
3. 先針對目標的Rows 進行 Lock ，防止其他 Process 同時修改衝突。
4. 產生這段SQL 對應的 undo 的 redo entry，放到 Log Buffer
5. 產生這段SQL 對應的 undo，放到 Buffer Cache
6. 產生這段SQL 的 redo entry ，放到 Log Buffer
7. 根據這段SQL 去異動資料區塊的資料
8. 如果有 commit ，LGWR會將 Log Buffer內的 Redo Entry寫入  Online Redo Logfile
9. 結束

#### 注意:

1. 資料異動前，要先產生該筆資訊的 Redo Entry (重作項目)，這是因為如果資料庫發生異常，可以透過 Redo Entry 恢復。<br>假設今天直接去Buffer Cache 修改資料 且不產生 Redo Entry ，此時發生停電當機。這時候因為buffer cache還未被DBWR 寫回Datafile，因此這筆更新會消失，但對於使用者來說，他已經提交(commit) 且資料庫也說完成，`導致資料庫ACID的 Durability (永久性) 失效。`<br>因此在修改 Buffer Cache之前，先產生一筆 Redo Entry ，當出現提交(commit)時，LGWR會將Log buffer 內所有的 Redo Log寫入 Online Redo Logfile (實際檔案, I/O operations)。即便這時候停電，重開機時 Oracle Server仍可以從寫入 Online Redo Logfile 中找出當初做了甚麼，以此來重做一遍。

2. 更新一筆資料前，`更應該要產生 Undo 的資料`， 如果你的這筆SQL 執行到一半發生錯誤，就必須透過 Undo的方式 Rollback。如果沒有 Undo 導致無法RollBack，這樣就`缺少資料庫 ACID的 Atomicity (原子性): 一筆資料只能全部成功或是全部失敗。`






### 名詞解釋


<a id="1"> </a>
- [[返]](#b1) 邏輯結構使資料庫更有效率原因 :  
  1. 每次讀取資料使用 Block (8kb)，一次拿一塊，而不是一個一個 Byte慢慢讀。
  2. 連續的 Extent 可以讓硬碟讀寫時不用跳來跳去,速度比較快。
  3. 配合 Buffer Cache 記憶體區塊，大幅減少讀寫硬碟的次數。

<a id="2"> </a>
- [[返]](#b2) Instance Recovery : 當資料庫異常關閉(如當機、斷電)時,重啟後自動執行的恢復程序。主要功能:
  
  - **前滾(Roll Forward)**: 利用 Redo Log 重新執行已提交但尚未寫入 datafile 的交易
  - **回滾(Roll Back)**: 撤銷未提交的交易,確保資料一致性
  - **目的**: 將資料庫恢復到異常發生前的穩定狀態
  
<a id="3"> </a>
- [[返]](#b3) Dirty Cache : Buffer Cache 的內容是從 datafile 讀取的,所以正常情況下兩邊的內容應該要一致。但如果今天使用者異動了資料,導致 Buffer Cache 中的某一個 Block 與 datafile 內容不同時,此區塊就是 Dirty Cache (髒緩衝)。
  
  - **處理方式**: 由 `DBWR 背景程序定期`或在 `特定條件下` 將 Dirty Cache 寫回 datafile



## DBA 如何管理

### 日常備份

### 備份偵測＆驗證

### 資料庫行為偵測

### 監控

### 空間管理



# Oracle 錯誤

Oracle錯誤統一都是會出現 `ora-XXXXX` 的樣式。

## <a href="https://peienn.github.io/posts/markdown/templates.html?file=posts/markdown/OracleError.md" > Oracle Error Code 紀錄 </a>

 

## ORA-12519, TNS:no appropriate service handler found

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

## ORA-01653: unable to extend table

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



## ORA-28040 No matching authentication protocol

問題 : Client端以往都是連線Oracle 11g, Oracle 12c, 但今天連線的DB換成 Oracle 19c後就跳出 `ORA-28040`。

原因 : 因為兩邊的 `密碼驗證協議` 不兼容，導致Client無法連線使用OracleDB


解決方法: 進入Oracle Server，切換到 $ORACLE_HOME/network/admin下，找出sqlnet.ora (如果沒有的話可以自行建立)。
在裡面加入  SQLNET.ALLOWED_LOGON_VERSION_SERVER=8

- SQLNET.ALLOWED_LOGON_VERSION_SERVER=8 : 這台機器<u>接受連線時</u>允許的最低登入版本
- SQLNET.ALLOWED_LOGON_VERSION_CLIENT=8 : 這台機器<u>連線出去時 (ex: DB Link) </u>允許的最低登入版本。

加入後，Client端測試就會由 ORA-28040 變成 ORA-01017 

## ORA-01017 invalid username/password; logon denied

由 ORA-28040 轉變成的 ORA-01017，基本上是因為密碼的認證演算法的不同導致。

因為之前`未允許低版本`可連線，導致該時所建立的帳號，其密碼版本是 11G, 12C (高版本)

現在修改成允許低版本的Client 也可以連線，但會因為低版本Client 使用的密碼版本可能只支援 10G甚至更舊。

此時就會引發 ORA-01017 logon denied。

**解決方法** : `重新設定密碼`

允許低版本 Client可以登入後，要將之前所建立的帳號 `重新設定密碼`，然後你就會發現帳號的密碼版本被修改為10G, 11G, 12C

這時候低版本Client也可以連線，而問題就解決了


---
