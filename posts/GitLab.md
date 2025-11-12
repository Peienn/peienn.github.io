### Setup-GitLab

**[Step by step Teaching](https://medium.com/@peienwutech/gitlab-ci-cd-%E5%BE%9Egitlab%E5%BB%BA%E7%BD%AE%E9%96%8B%E5%A7%8B-23d971cacf3c)**


# 主要流程
## 1. 架設 GitLab Server (Docker)
## 2. 架設 GitLab Runner (Docker) 並建立 Runner


# GitLab 與 Runner 的關係

在 GitLab CI/CD 流程中，**GitLab** 與 **Runner** 是兩個核心組件，它們的關係如下：

---

## 1. GitLab
- GitLab 是 **版本控制平台 + CI/CD 管理系統**
- 功能：
  - 儲存程式碼（Git repository）
  - 管理專案、權限與協作
  - 定義 CI/CD pipeline（透過 `.gitlab-ci.yml`）
  - 負責 **排程、管理與監控 pipeline 執行狀態**

> 簡單來說，GitLab 是「指揮中心」，負責決定什麼任務要執行。

---

## 2. GitLab Runner
- Runner 是 **實際執行 pipeline job 的 agent**
- 功能：
  - 接收 GitLab 分配的 job
  - 在指定的 executor（如 Docker、Shell、Virtual Machine）中執行 job
  - 將結果回傳給 GitLab

> 簡單來說，Runner 是「工人」，真正幫你跑程式、測試、部署。

---

## 3. GitLab 與 Runner 的互動流程

1. 開發者 push 代碼到 GitLab 專案
2. GitLab 解析 `.gitlab-ci.yml`，生成 pipeline
3. Pipeline 被拆成一個個 job
4. GitLab 將 job 發送給 **可用的 Runner**
5. Runner 在指定環境中執行 job（測試、建置、部署等）
6. Runner 將執行結果回報給 GitLab
7. GitLab 顯示 pipeline 狀態（成功/失敗/日誌）


