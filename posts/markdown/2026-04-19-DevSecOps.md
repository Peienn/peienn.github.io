# 在 GitLab CI/CD 中整合 Trivy 實現容器映像漏洞自動化掃描

## 前言

當團隊開始大量使用容器化部署後，一個常見的安全盲點就是「映像檔內的漏洞」。我們可能用了過時的 base image、引入了有 CVE 的套件，卻渾然不覺地推上了 production。

傳統做法是定期手動掃描，但這與 DevOps 的自動化精神背道而馳。真正的 DevSecOps 應該是：**每一次 push 都自動執行安全掃描，發現高風險漏洞時直接阻擋部署**。

本文將示範如何在 GitLab CI/CD pipeline 中整合 Trivy，實現容器映像的自動化漏洞掃描，讓安全檢查成為開發流程中「看不見但一直存在」的守護者。

## 為什麼選擇 Trivy？

市面上有不少容器掃描工具，例如 Clair、Anchore、Snyk 等。Trivy 之所以成為許多團隊的首選，有幾個原因：

- **零配置即可使用**：不需要額外啟動 server 或 database
- **速度快**：第一次掃描下載漏洞資料庫後，後續掃描通常在數秒內完成
- **支援多種掃描目標**：container image、filesystem、git repository、Kubernetes 配置
- **持續更新的漏洞資料庫**：涵蓋 NVD、Red Hat、Debian、Alpine 等多個來源

先在本地測試一下：

```bash
# 安裝 Trivy（macOS）
brew install trivy

# 掃描一個映像檔
trivy image python:3.9-slim

# 只顯示 HIGH 和 CRITICAL 等級的漏洞
trivy image --severity HIGH,CRITICAL python:3.9-slim
```

## 建立 GitLab CI/CD Pipeline 整合

接下來是重點：把 Trivy 整合進 CI/CD pipeline。以下是一個實用的 `.gitlab-ci.yml` 範例：

```yaml
stages:
  - build
  - security
  - deploy

variables:
  IMAGE_NAME: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  TRIVY_SEVERITY: "HIGH,CRITICAL"
  TRIVY_EXIT_CODE: "1"  # 發現漏洞時回傳非零，使 pipeline 失敗

build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $IMAGE_NAME .
    - docker push $IMAGE_NAME

trivy-scan:
  stage: security
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code $TRIVY_EXIT_CODE --severity $TRIVY_SEVERITY --no-progress $IMAGE_NAME
  allow_failure: false  # 關鍵：漏洞掃描失敗時阻擋後續 deploy

deploy:
  stage: deploy
  script:
    - echo "Deploying to production..."
  only:
    - main
```

這個設定的關鍵在於 `--exit-code 1`，當發現指定等級的漏洞時，Trivy 會回傳非零值讓 job 失敗，進而阻擋 deploy stage 執行。

## 產出結構化報告供後續分析

只是讓 pipeline 失敗還不夠，我們需要可追蹤、可分析的報告。Trivy 支援多種輸出格式，建議同時產出人類可讀和機器可讀的版本：

```yaml
trivy-scan:
  stage: security
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    # 產出 JSON 報告供後續工具分析
    - trivy image --format json --output trivy-report.json $IMAGE_NAME
    # 產出 table 格式寫入 log，方便開發者直接查看
    - trivy image --format table --severity $TRIVY_SEVERITY --exit-code $TRIVY_EXIT_CODE $IMAGE_NAME
  artifacts:
    paths:
      - trivy-report.json
    reports:
      container_scanning: trivy-report.json
    expire_in: 30 days
```

GitLab 會自動解析 `container_scanning` 報告，在 Merge Request 頁面顯示安全摘要，讓 code reviewer 一目瞭然。

## 處理誤報與已知風險的白名單機制

實務上，不是所有漏洞都需要立刻處理。有些是誤報，有些在特定情境下風險極低。Trivy 提供 `.trivyignore` 檔案來管理例外：

```bash
# .trivyignore
# 格式：CVE編號 + 可選的註解

# 這個 CVE 在我們的使用情境下無影響（已評估）
CVE-2023-12345

# 等待上游修復，預計下個 sprint 處理
CVE-2024-67890
```

將這個檔案放在專案根目錄，Trivy 會自動套用。**但請務必定期檢視這個清單**，避免變成「漏洞墳場」。建議搭配每月的安全檢視會議，重新評估每一條忽略項目。

## 結論與行動建議

將 Trivy 整合進 GitLab CI/CD 只是 DevSecOps 的起點，但這一步能立即帶來顯著的安全提升：

1. **今天就做**：先在一個非關鍵專案試行，熟悉 Trivy 的輸出和設定
2. **漸進式推廣**：初期可設 `allow_failure: true`，收集數據後再轉為強制阻擋
3. **搭配通知**：整合 Slack 或 Teams，讓團隊即時收到掃描結果
4. **定期更新 base image**：掃描只是發現問題，根本解法是保持 image 更新

安全不是一次性的任務，而是持續的過程。讓自動化工具替你守住第一道防線，你才能專注在更有價值的事情上。

---
date: 2026-04-19
topic: DevSecOps
tags: [devops, security, trivy, gitlab-ci, container-scanning, vulnerability-management]
---