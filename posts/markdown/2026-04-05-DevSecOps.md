# 在 CI/CD Pipeline 中整合 SAST 工具：以 Semgrep 為例的實戰指南

## 前言

當團隊開始實踐 DevSecOps 時，最常遇到的第一個問題就是：「安全檢測應該在 Pipeline 的哪個階段執行？用什麼工具？」許多工程師嘗試導入 SAST（Static Application Security Testing）工具後，卻發現掃描時間過長拖慢部署、誤報率太高導致團隊疲乏、或是規則難以客製化而無法符合專案需求。

本文將以開源工具 Semgrep 為例，分享如何在 CI/CD Pipeline 中有效整合 SAST，避免常見的導入陷阱，讓安全掃描真正成為開發流程的助力而非阻力。

## 為什麼選擇 Semgrep 作為 SAST 工具

市面上 SAST 工具眾多，包括 SonarQube、Checkmarx、Snyk Code 等。Semgrep 之所以適合作為 DevSecOps 入門工具，主要有以下優勢：

- **速度快**：採用增量掃描，平均專案掃描時間在 30 秒內完成
- **規則易懂**：使用類似程式碼的 pattern 語法，工程師可快速撰寫自訂規則
- **低誤報率**：支援 taint tracking 和 constant propagation，減少無意義的警報
- **免費開源**：OSS 版本即可滿足多數團隊需求

安裝方式相當簡單：

```bash
# 使用 pip 安裝
pip install semgrep

# 或使用 Docker
docker run --rm -v "${PWD}:/src" returntocorp/semgrep semgrep --config=auto /src
```

## 在 GitLab CI 中整合 Semgrep

以下是一個實際可用的 GitLab CI 設定範例，展示如何將 Semgrep 整合到 Pipeline 中：

```yaml
# .gitlab-ci.yml
stages:
  - test
  - security
  - build
  - deploy

semgrep-scan:
  stage: security
  image: returntocorp/semgrep:latest
  variables:
    SEMGREP_RULES: >-
      p/default
      p/owasp-top-ten
      p/security-audit
  script:
    - semgrep ci --json --output=semgrep-results.json
  artifacts:
    reports:
      sast: semgrep-results.json
    paths:
      - semgrep-results.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  allow_failure: false
```

關鍵設定說明：
- 將安全掃描放在 `test` 之後、`build` 之前，確保問題在早期被發現
- 使用 `allow_failure: false` 強制 Pipeline 在發現高風險漏洞時中斷
- 輸出 JSON 格式方便後續整合至 Security Dashboard

## 處理誤報與客製化規則

導入 SAST 工具最令人沮喪的就是誤報（False Positive）。Semgrep 提供多種方式處理：

**方法一：使用 inline 註解忽略特定行**

```python
# 這是刻意為之的測試用 hardcoded credential
password = "test123"  # nosemgrep: hardcoded-credential
```

**方法二：建立專案層級的忽略清單**

```yaml
# .semgrep/settings.yml
exclude:
  - "tests/**"
  - "**/*_test.go"
  - "**/vendor/**"
  
# 忽略特定規則
rules:
  - id: generic.secrets.security.detected-generic-secret
    paths:
      exclude:
        - "config/examples/**"
```

**方法三：撰寫符合團隊規範的自訂規則**

```yaml
# .semgrep/custom-rules.yml
rules:
  - id: custom.no-fmt-printf-in-handlers
    pattern: fmt.Printf(...)
    paths:
      include:
        - "**/handlers/**"
    message: "Handler 中請使用 structured logging，避免使用 fmt.Printf"
    severity: WARNING
    languages: [go]
```

## 建立漸進式導入策略

一次性開啟所有規則並設為 blocking 是常見的導入失敗原因。建議採用漸進式策略：

```bash
# 第一週：僅啟用高嚴重性規則，且設為 warning only
semgrep --config=p/default --severity=ERROR --no-error

# 第二週：開始收集 metrics，觀察誤報率
semgrep --config=p/default --metrics=on --json > results.json

# 第三週後：逐步將規則設為 blocking
semgrep --config=p/default --error --severity=ERROR,WARNING
```

同時建議在 Slack 或 Teams 設定通知，讓團隊逐漸習慣安全回饋：

```bash
# 結合 jq 擷取關鍵資訊並發送通知
FINDINGS=$(cat semgrep-results.json | jq '.results | length')
curl -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"Semgrep 發現 ${FINDINGS} 個潛在問題\"}"
```

## 結論與行動建議

將 SAST 整合進 CI/CD Pipeline 是 DevSecOps 實踐的重要一步，但成功的關鍵不在於工具本身，而在於如何讓團隊接受並持續使用。

**建議的下一步行動：**

1. 先在單一專案試行 Semgrep，使用 `--config=auto` 自動偵測語言並套用適合的規則集
2. 觀察兩週，統計誤報率，並建立團隊專屬的忽略清單
3. 與開發團隊共同討論哪些規則應設為 blocking
4. 逐步擴展至其他專案，並考慮導入 Semgrep App 集中管理掃描結果

記住，DevSecOps 的目標是讓安全成為開發流程的一部分，而非額外負擔。選擇對的工具、採用漸進式導入、並持續根據團隊回饋調整，才是長久之道。

---
date: 2026-04-05
topic: DevSecOps
tags: [devops, sast, semgrep, cicd, security, gitlab]
---