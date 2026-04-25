# 當 Error Budget 燒完了，團隊該怎麼辦？建立有效的 Error Budget Policy 實戰指南

## 前言

你的團隊已經定義了 SLO，也設定好了 SLI 的監控儀表板，Error Budget 的燒毀率也一目了然。但某天早上，你發現 Error Budget 只剩下 5%，而這個月才過了一半——接下來該怎麼辦？

很多團隊在導入 SLO 時，把重心放在「如何定義」與「如何測量」，卻忽略了最關鍵的一環：**Error Budget Policy**。沒有明確的政策，當 Error Budget 耗盡時，團隊往往陷入爭論：是該繼續推新功能，還是全力修 bug？這篇文章將帶你建立一套可執行的 Error Budget Policy，讓 SLO 真正成為團隊決策的依據。

## 什麼是 Error Budget Policy？

Error Budget Policy 是一份正式文件，明確定義當 Error Budget 處於不同狀態時，團隊應該採取的具體行動。它不是技術規格，而是一份**團隊契約**，需要 Dev、Ops、PM 三方共同同意。

一份基本的 Policy 應該回答以下問題：

- Error Budget 剩餘多少時觸發警告？
- 誰有權決定暫停功能開發？
- 觸發後要執行哪些具體措施？
- 如何判定何時可以解除限制？

以下是一個 Policy 文件的範例結構：

```yaml
# error-budget-policy.yaml
service: payment-api
slo_target: 99.9%
policy_version: "1.2"
escalation_thresholds:
  - level: warning
    budget_remaining: 30%
    actions:
      - 每日 Error Budget Review 會議
      - 暫停非必要的變更部署
  - level: critical
    budget_remaining: 10%
    actions:
      - 凍結所有功能開發
      - 全員投入可靠性改善
      - 每次部署需 SRE 審核
  - level: exhausted
    budget_remaining: 0%
    actions:
      - 僅允許修復性部署
      - 啟動事後檢討流程
```

## 設計分級響應機制

有效的 Policy 不是非黑即白的開關，而是分級響應。建議至少設計三個等級：

**Warning（30% 以下）**：這是早期警告。團隊應該開始關注，但不需要恐慌。此階段的重點是提高警覺，減少高風險變更。

```bash
# 在 CI/CD pipeline 中加入檢查
if [ "$ERROR_BUDGET_REMAINING" -lt 30 ]; then
  echo "⚠️ Error Budget Warning: ${ERROR_BUDGET_REMAINING}% remaining"
  echo "Deployment requires additional review"
  # 發送 Slack 通知給 on-call
  curl -X POST "$SLACK_WEBHOOK" -d '{"text":"Error Budget Warning triggered"}'
fi
```

**Critical（10% 以下）**：進入緊急狀態。功能開發應該暫停，團隊資源轉向改善系統穩定性。這個階段要有明確的「解凍條件」，例如連續三天 Budget 燒毀率恢復正常。

**Exhausted（0%）**：Error Budget 耗盡代表你已經違反對用戶的承諾。此時應該只允許能直接改善 SLI 的變更進入生產環境。

## 用 Prometheus + Grafana 實作自動化監控

手動追蹤 Error Budget 不切實際，你需要自動化。以下是使用 Prometheus 計算 Error Budget 剩餘百分比的範例：

```promql
# 計算過去 30 天的 Error Budget 消耗
# 假設 SLO 是 99.9%，允許的錯誤預算是 0.1%

# 實際錯誤率
(
  sum(rate(http_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
) 

# Error Budget 剩餘百分比
(
  1 - (
    (sum(rate(http_requests_total{status=~"5.."}[30d])) / sum(rate(http_requests_total[30d])))
    /
    0.001  # 允許的錯誤率 (1 - 0.999)
  )
) * 100
```

在 Grafana 中設定 Alert Rule，當剩餘百分比跌破閾值時自動通知：

```yaml
# grafana-alert-rule.yaml
groups:
  - name: error_budget_alerts
    rules:
      - alert: ErrorBudgetCritical
        expr: error_budget_remaining_percent < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error Budget Critical: {{ $value }}% remaining"
```

## 讓 Policy 融入日常開發流程

Policy 寫得再好，沒人遵守也沒用。關鍵是讓它融入團隊的日常工作流程：

1. **每週 Review**：在週會中花 5 分鐘檢視 Error Budget 儀表板
2. **PR 檢查**：在 Pull Request template 加入 Error Budget 狀態確認
3. **部署門禁**：當處於 Critical 狀態時，CI/CD 自動要求額外審核

```markdown
<!-- .github/pull_request_template.md -->
## Pre-deploy Checklist
- [ ] Error Budget 狀態已確認（目前: ____%）
- [ ] 若 < 30%，已通知 Tech Lead
- [ ] 此變更的 rollback 計畫已準備
```

## 結論與行動建議

Error Budget Policy 是讓 SLO 從「好看的數字」變成「實際決策工具」的關鍵。建議你現在就採取以下步驟：

1. **本週**：盤點目前的 Error Budget 監控是否完整
2. **下週**：召集 Dev/Ops/PM 討論並起草第一版 Policy
3. **本月**：在 CI/CD 中實作至少一個自動化檢查點

記住，Policy 不需要一開始就完美。從簡單的分級響應開始，根據實際運作經驗持續迭代。當整個團隊都理解「Error Budget 剩 10% 代表什麼」時，SLO 才真正發揮了它的價值。

---
date: 2026-04-25
topic: SLO / SLI / Error Budget
tags: [devops, sre, slo, error-budget, prometheus, reliability]
---