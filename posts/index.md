Index (索引) in Database (PostgreSQL 為例)



# Index 介紹 (What)


( 無 Index) <br>
使用資料庫時，我們常常會需要去資料庫裡面查詢資料，一般情況下，資料庫預設是全局掃描，也就是說從第一筆到最後一筆都看過後，將符合需求的回傳給使用者。但是如果今天資料筆數有1000萬筆呢? 

`掃描1000萬筆資料之後才回傳，速度會非常慢，對吧!` 

這時候大家就想出一個方法來提升查詢速度，那就是 Index 。

主要方法就是讓資料庫 `不必每次從頭掃描` 整個資料表，而是透過 Index 快速定位資料位置。因此大家介紹時都會將 Index 比喻成 "書本的目錄"，資料是用 `查詢` 的而不是`一個一個搜尋` 

**Index 核心理念 :  "加速資料查詢"**

# Index 使用時機 (When)

1. 頻繁查詢的欄位 : 
    - 包含搜尋條件 `(select..from.. where..;)`
    - 查詢整張表就不需要 `(select * from table;)`
2. 資料量龐大 : 如前面介紹，要避免1000萬筆資料都看過才能回傳
3. 常用作排序或分組的欄位 (OrderBy, GroupBy) : 省去排序的時間

不適用的時機 : 

1. 頻繁寫入的欄位或表 : 索引也是需要維護的，一直修修改改會造成額外許多成本
2. 小型資料表 : 速度本來就快，不需要額外維護索引。
3. 低選擇性欄位 : 例如Boolean欄位、少量不同值的欄位，效果很差



# Index 實踐原理 (How)

為甚麼透過 Index 就可以讓資料庫從全局掃描，變成是像目錄般的查詢呢? <br>
工程師應該都知道

- 要空間 ? 那你就要放棄時間
- 要時間 ? 那你就要放棄空間

所以 Index 實際上就是要`額外花費空間`去建置一個結構，這個結構通常是用B+Tree。在這個結構中去紀錄索引值以及實際位址。這樣當我們要進行查詢時，就可以透過B+ Tree的架構特性來縮短查詢時間 O(logN)。


簡單舉例 : 

今天我們建立了一個 Table : user ，並且在裡面插入了五筆資料

在資料庫內會針對這個Table 會建立一個資料頁 (Heap Table)，並且將這個資料頁切成固定大小的頁面 (Block/Page, 通常8KB)，每一個Block 裡面會有很多列 (Row)，用來儲存真正的資料。

如果我們去搜尋其中一筆資料，那資料庫就會在Heap Table內 逐筆的檢查。

---

接下來，假設我們常常會用到mail當作條件篩選，因此以mail 建立一個Index。

這時候，資料庫會幫我們建立一個B+ Tree的結構，並將原本五筆資料的 mail作為排序。此樹的Leaf 只會包含每一筆資料的mail以及TID，而其他欄位不會被放入 (因為是用mail作為Index)，。 

如果此時我們要去搜尋其中一筆資料，那資料庫就會先去 B+Tree 搜尋，找到符合條件的再根據 TID 去Heap Table 找真正的資料。


![123](index.png)

---

## 其他說明


在PostgreSQL中，有一種抽象物件叫做 **"Relation**，裡面記錄著資料庫的物件的 What、How、Where。
- What : 資料庫物件是甚麼類型 （例如：table、index、view）
- How : 怎麼存這個物件
- Where : 物件存放在哪

SQL 語法中建立 Table ，在PostgreSQL的世界就是建立一個 Relation；每一個 Table/Relation 都是由多個 Page 組成，每個 Page 約 8K。 寫到 Page 裡面的東西就是真實寫到硬碟裡了。

所以每一筆SQL 都需要去查找對應的 Relation 來確認實體位址，才能進行操作。 Relation都寫在 system catalog內； system catalog是由多個 Table、System View、index..組合而成。


舉例來說: `select * from user;`  

當下了這一段SQL，資料庫首先會解析出 table 叫做 user ，在去 system catalog 查詢 user 這個 table 的 relation 紀錄，從記錄內找出這個 table的資訊都寫在哪些實際物理檔案，最後在將其回傳

Postgre 中的 Heap 是個形容詞，代表 "不排序，有空位就儲存"
---

### SQL 操作 對應 資料庫底層行為

1. 啟動資料庫服務 : 將物理檔案打開後組合成邏輯檔案 (Heap Table)，物理檔案包含資料檔案、索引檔案等等，並透過Buffer Pool (緩衝區) 持續的管理和使用資料。

2. 建立Table  : 
    - 在system catalog 新增一筆 Relation 紀錄，描述這個 Table。
    - 建立對應的實體檔案 (file)

3. 插入資料 : 
    - 透過system catalog 找到 Table 對應的  heap relation 資訊。
    - 在 heap relation 裡面找一個有空位的 heap page
    - 把 row 轉換成 tuple格式後寫入 heap page
    - 同時寫一筆 WAL (Write-Ahead Log)，確保crash recovery
    - 更新 index (如果有index)


4. 建立 Index : 
    - 在system catalog 新增一筆  index relation
    - 建立對應的實體檔案
    - 根據SQL的table，找出其 heap relation 內的資料，掃描所有ROW + 排序 後寫入 index page。


5. 查詢 Table 不用 Index : 直接去找到對應的 Heap Table ，對底下的每一個 heap page 的每一筆資料進行檢查。

6. 查詢 Table 透過 Index : 先到索引檔案裏面使用B+ Tree搜尋，再透過TID去Heap Table找到資料。

---


1. 常用作排序或分組的欄位 (OrderBy, GroupBy) : 
    - order by的欄位沒有Index的情況下進行查詢，是先找出符合條件的資料、進行排序，最後傳遞。
    - order by的欄位是有index的情況下進行查詢，直接去 Index裡面查詢後就可以回傳，`省略排序`。因為Index所用的B+Tree 本身就有排序的功能。
    - 所以`常用來判斷搜尋`的欄位，都會建立index



2. PostgreSQL 使用 MVCC，更新或刪除資料時，舊版本不會立即刪除，而是標記為失效。雖然 autovacuum 定期清理部分無效資料，但無法完全壓縮索引頁面空間。
結果導致索引變得碎片化、膨脹（bloat），影響查詢效率和空間使用。

    解決方法： 使用 REINDEX，重新建立索引，整理有效資料，提高空間利用率和效能。
    檢查方法： 可透過 pg_stat_user_indexes 或 pgstatindex() 監測膨脹狀況。


3. 索引頁面空間 : B-tree 索引的Leaf Node，會被切割成多個用來存放Key + tuple identifier(TID) 每個預設為8KB的 索引頁面。這些頁面是索引實際儲存資料的基本單位。[可以想像B-tree的Leaf 被切成多個區塊，1個區塊就是一個頁面

4. 可以用EXPLAIN 查看table是如何scan的
