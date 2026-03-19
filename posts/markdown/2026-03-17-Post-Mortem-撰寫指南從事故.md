# Post-Mortem 撰寫指南：打造無責備文化，讓每次事故都成為團隊進化的養分

## 前言

凌晨三點，警報大作，整個團隊被迫從床上爬起來處理線上事故。經過三小時的奮戰，服務終於恢復正常。但接下來呢？是找出「罪魁禍首」然後懲處，還是深入挖掘系統性問題？

在 DevOps 文化中，Post-Mortem（事後檢討報告）不是用來追究責任的審判書，而是團隊從失敗中學習的珍貴機會。Google、Netflix、Etsy 等科技巨頭都將 Blameless Post-Mortem（無責備事後檢討）視為工程文化的核心。本文將帶你掌握撰寫高品質 Post-Mortem 的技巧，讓每次事故都能轉化為團隊成長的動力。

## 為什麼要採用無責備文化？

傳統的事故處理方式往往聚焦在「誰犯了錯」，但這種做法會導致幾個嚴重問題：

- **資訊隱藏**：工程師害怕被責備，傾向隱瞞細節
- **表層修復**：只處理直接原因，忽略系統性問題
- **創新停滯**：團隊變得保守，不敢嘗試新方法

無責備文化的核心理念是：**人會犯錯是必然的，我們要改善的是系統與流程，而非懲罰個人**。當工程師知道誠實分享不會帶來負面後果時，你才能獲得最完整的事故資訊。

```yaml
# 心態轉換對照
傳統思維: "是誰部署了那個有問題的程式碼？"
無責備思維: "為什麼我們的系統允許有問題的程式碼進入生產環境？"
```

## Post-Mortem 的標準結構

一份完整的 Post-Mortem 應該包含以下幾個核心區塊。建議在團隊內建立標準模板，確保每次事故都能被系統性地記錄：

```markdown
# Post-Mortem: [事故簡述]
**日期**: YYYY-MM-DD
**嚴重等級**: P1/P2/P3
**撰寫者**: [姓名]
**事故持續時間**: [開始時間] - [結束時間]

## 摘要
一段話描述發生了什麼事、影響範圍、如何解決

## 影響評估
- 受影響用戶數：
- 財務損失估計：
- SLA 違反情況：

## 時間軸
以時間順序記錄關鍵事件

## 根本原因分析
深入分析為什麼會發生

## 改善行動項目
具體的後續改善措施

## 經驗學習
這次事故教會我們什麼
```

許多團隊使用專門的工具來管理 Post-Mortem，例如：

```bash
# 常見的 Post-Mortem 管理工具
- Incident.io      # 整合 Slack 的事故管理平台
- Blameless        # 專業的 SRE 平台
- PagerDuty        # 內建 Post-Mortem 功能
- Notion/Confluence # 通用文件協作工具搭配模板
```

## 運用 5 Whys 進行根本原因分析

根本原因分析（Root Cause Analysis）是 Post-Mortem 的靈魂。最常用的技巧是「5 Whys」——持續追問為什麼，直到找出系統性問題：

```
事故：用戶無法登入系統

Why 1: 為什麼用戶無法登入？
→ 因為認證服務回傳 500 錯誤

Why 2: 為什麼認證服務回傳 500 錯誤？
→ 因為資料庫連線池耗盡

Why 3: 為什麼連線池會耗盡？
→ 因為有個查詢沒有正確關閉連線

Why 4: 為什麼有問題的程式碼會進入生產環境？
→ 因為 Code Review 沒有發現這個問題

Why 5: 為什麼 Code Review 沒有發現？
→ 因為我們沒有針對資料庫連線的檢查清單

根本原因：Code Review 流程缺乏資料庫操作的檢查項目
```

注意，根本原因絕對不應該是「某人犯了錯」。如果你的分析停在人為錯誤，請繼續追問：為什麼系統允許這個錯誤發生？

## 制定有效的改善行動項目

Post-Mortem 最重要的產出是改善行動項目（Action Items）。好的行動項目應該符合 SMART 原則：

```yaml
# 好的行動項目範例
- title: "新增資料庫連線池監控告警"
  owner: "@david"
  deadline: 2026-03-24
  priority: P1
  jira_ticket: OPS-1234
  
- title: "更新 Code Review Checklist，加入資料庫連線檢查"
  owner: "@sarah"
  deadline: 2026-03-20
  priority: P2
  jira_ticket: OPS-1235

- title: "撰寫資料庫連線最佳實踐文件"
  owner: "@mike"
  deadline: 2026-03-31
  priority: P3
  jira_ticket: OPS-1236
```

建議使用以下指令追蹤行動項目的完成狀況：

```bash
# 在週會中檢視未完成的 Post-Mortem 行動項目
# 可整合到 CI/CD 或定期報告中

#!/bin/bash
# 範例：從 Jira 拉取 Post-Mortem 相關 tickets
jira-cli issue list \
  --project OPS \
  --label post-mortem \
  --status "In Progress" \
  --format table
```

## 建立持續學習的回饋循環

單一的 Post-Mortem 價值有限，真正的力量來自於累積與分享。建議團隊建立以下機制：

1. **事故資料庫**：將所有 Post-Mortem 存放在可搜尋的平台
2. **定期回顧會議**：每月檢視事故趨勢與改善進度
3. **跨團隊分享**：重大事故的 Post-Mortem 應該公開給全公司學習

```bash
# 使用 Git 管理 Post-Mortem 文件
mkdir -p docs/post-mortems/2026
cd docs/post-mortems/2026

# 依日期與事故編號命名
touch 2