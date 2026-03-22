# Terraform State 鎖定衝突：多人協作時的終極解決方案

## 前言

當團隊規模從單人擴展到多人協作時，Terraform 使用者幾乎都會遇到一個令人頭痛的問題：State 鎖定衝突。你可能曾經看過這段熟悉的錯誤訊息：

```
Error: Error acquiring the state lock
Lock Info:
  ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Path:      s3://my-bucket/terraform.tfstate
  Operation: OperationTypePlan
  Who:       colleague@hostname
  Version:   1.7.0
  Created:   2026-03-22 10:15:30.123456 +0000 UTC
```

這個問題看似簡單，但處理不當可能導致 State 檔案損壞、基礎設施配置不一致，甚至造成生產環境事故。本文將深入探討 State 鎖定機制的原理，以及在實際團隊協作中如何優雅地解決這類衝突。

## State 鎖定機制的運作原理

Terraform 的 State 鎖定是一種分散式鎖機制，確保同一時間只有一個操作能修改 State 檔案。當你執行 `terraform plan`、`apply` 或 `destroy` 時，Terraform 會先嘗試取得鎖定。

以最常見的 S3 + DynamoDB 後端為例，鎖定資訊會寫入 DynamoDB：

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/infrastructure.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

DynamoDB 表需要有 `LockID` 作為 Partition Key。當鎖定發生時，Terraform 會在此表中建立一筆記錄，記載操作者、時間與操作類型。

## 常見的鎖定衝突情境與診斷

在實務中，鎖定衝突通常來自以下幾種情境：

**情境一：同事正在執行操作**
這是最正常的情況，等待對方完成即可。你可以透過以下指令查詢目前的鎖定狀態：

```bash
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "my-terraform-state/prod/infrastructure.tfstate"}}' \
  --region ap-northeast-1
```

**情境二：操作中斷留下的殭屍鎖**
當 `terraform apply` 因為網路中斷、終端機關閉或 Ctrl+C 強制終止時，鎖定可能沒有被正確釋放。這時候需要手動介入處理。

**情境三：CI/CD Pipeline 重複觸發**
多個 Pipeline 同時執行相同的 Terraform 配置，這屬於架構設計問題，需要從根本上解決。

## 安全解除鎖定的標準流程

當確認是殭屍鎖時，可以使用 `force-unlock` 指令解除：

```bash
# 先確認鎖定資訊中的 ID
terraform force-unlock xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**重要提醒**：執行此指令前，務必確認：

1. 透過即時通訊確認沒有同事正在操作
2. 檢查 CI/CD 系統是否有正在執行的 Job
3. 確認 Lock ID 與錯誤訊息中的完全一致

若你使用的是 Terraform Cloud 或 Enterprise，可以直接在 Web UI 中解除鎖定，操作紀錄也會被完整保留。

## 預防勝於治療：團隊協作最佳實踐

與其頻繁處理鎖定衝突，不如從流程上預防：

**導入 State 檔案分割策略**
將大型基礎設施拆分為多個獨立的 State 檔案，降低衝突機率：

```
infrastructure/
├── network/          # VPC、Subnet 等，變動頻率低
├── compute/          # EC2、ECS 等，變動頻率中
├── database/         # RDS、ElastiCache 等，變動頻率低
└── application/      # Application 相關資源，變動頻率高
```

**在 CI/CD 中實作排隊機制**
以 GitHub Actions 為例，使用 `concurrency` 確保同一環境的部署不會並行：

```yaml
concurrency:
  group: terraform-${{ github.ref }}-${{ inputs.environment }}
  cancel-in-progress: false
```

**設定合理的鎖定超時時間**
在 Terraform 1.0+ 版本中，可以設定鎖定超時：

```bash
terraform apply -lock-timeout=5m
```

這讓 Terraform 在取得鎖定前等待，而非立即失敗。

## 結論與行動建議

State 鎖定衝突是 Terraform 多人協作的必經之路，但透過正確理解機制與建立團隊規範，可以大幅降低其影響。建議你：

1. **今天就做**：確認團隊的 Backend 配置是否正確啟用 DynamoDB 鎖定
2. **本週完成**：建立團隊內部的 `force-unlock` 操作 SOP，包含確認清單
3. **本月規劃**：評估現有 State 檔案結構，考慮是否需要拆分以降低衝突

記住，`force-unlock` 是最後手段，而非日常操作。當你發現團隊頻繁需要解鎖時，這是一個警訊——是時候重新審視你們的 IaC 協作流程了。

---
date: 2026-03-22
topic: Terraform
tags: [devops, terraform, infrastructure-as-code, state-management, team-collaboration]
---