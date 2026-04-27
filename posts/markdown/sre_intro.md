# 網站可靠性工程 (SRE)

由 Google 創造的職位，主要是透過軟體工程方法去管理系統和服務，確保服務可靠性、擴充性和效能。簡單說就是用寫程式 (自動化) 來取代以往的人工 (Toil) 維運。

`SRE is what happens when you ask a software engineer to design an operations team.`


SRE 中的 **Toil（雜務）**，指的是：

- 手動、重複性的操作
- 沒有長期價值的工作
- 可以被自動化取代的任務

例如：每天早上手動巡檢伺服器狀態、每次部署都要人工執行的步驟、收到告警後手動重啟服務等。

## 核心職責

1. 自動化維運 (Automation)：撰寫自動化工具，減少日常手動維運任務
2. 監控與告警 (Monitoring)：建立指標、日誌和追蹤等可觀測性系統，監控服務健康狀態
3. 事故管理 (Incident Management)：快速偵測、回應與復原系統故障，並透過 Postmortem 找出根本原因
4. 容量規劃 (Capacity Planning)：預測流量成長，確保系統在高負載下仍能穩定運行
5. 可靠性設計 (Reliability Engineering)：參與系統架構設計，從源頭降低故障風險



---

## SRE vs DevOps vs 傳統 Ops

很多人搞不清楚這三個的差別，簡單整理如下：

| | 傳統 Ops | DevOps | SRE |
|---|---|---|---|
| 核心思維 | 穩定優先，避免變動 | 開發與維運協作 | 用工程方法管理可靠性 |
| 自動化程度 | 低，大量手動操作 | 中，CI/CD 為主 | 高，toil 消除為目標 |
| 出身背景 | 系統管理員 | 開發或維運皆有 | 軟體工程師 |
| 可靠性衡量 | 憑感覺 | 憑感覺 | SLO / Error Budget |


> DevOps 是一種**文化與流程**，SRE 是一種**具體實踐方式**。
> 
> Google ：「SRE 是 DevOps 的一種實作。」

---

前一系列（後端技術）是架設一個聊天室系統，此次將以該專案作為觀察的對象。


<figure style="text-align: center;">
  <img src="../images/SRE/arch.svg" alt="GitLab 架構圖" />
  <figcaption>聊天室專案架構圖</figcaption>
</figure>

- **Nginx 掛了**：所有用戶無法連線
- **Node.js (Server) 掛了**：Nginx流量導向至其他台，服務繼續。
- **Redis 掛了**：影響最廣，因為所有功能都依賴同一個 Redis 實例：
  - Pub/Sub 中斷 → 跨伺服器訊息無法廣播
  - Stream (MQ) 停止 → AI 分析功能無法使用
  - Cache 失效 → 快速讀取 50 筆功能失敗，需 fallback 至 PostgreSQL
  三個功能同時壞，blast radius 最大

- **PostgreSQL 掛了**：歷史訊息無法讀取
- **任一元件變慢**：用戶感受到訊息延遲

SRE 的工作就是：**在這些問題發生前偵測到，發生時快速處理，發生後不再重蹈覆轍。**


下一篇，將會從聊天室系統出發，定義第一個 SLO。