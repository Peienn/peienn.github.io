# Terraform State 鎖定衝突：多人協作的實戰解決方案

## 前言

當團隊從單人作業擴展到多人協作，Terraform 的 state 鎖定問題往往成為第一個絆腳石。你可能遇過這種情況：正準備執行 `terraform apply`，卻看到那令人沮喪的錯誤訊息——「Error acquiring the state lock」。更糟的是，前一位同事可能只是網路斷線，卻留下了一個幽靈鎖，阻擋整個團隊的部署流程。

這篇文章將深入探討 state 鎖定的運作機制，並提供實際可行的解決方案，讓你的團隊能夠順暢地進行協作部署。

## 理解 State Lock 的運作機制

Terraform 的 state lock 是一種防止並行修改的保護機制。當你執行 `plan`、`apply` 或 `destroy` 時，Terraform 會嘗試取得鎖定，確保同一時間只有一個操作能修改 state。

以 AWS S3 + DynamoDB 這個最常見的 remote backend 配置為例：

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

DynamoDB 表需要包含一個名為 `LockID` 的 partition key，Terraform 會在此寫入鎖定資訊，包含操作者、時間戳記與操作類型。

## 診斷鎖定衝突的根本原因

當遇到鎖定錯誤時，首先要判斷這是「合理的鎖定」還是「殘留的幽靈鎖」。錯誤訊息通常會顯示：

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        a1b2c3d4-5678-90ab-cdef-example12345
  Path:      my-terraform-state/prod/infrastructure.tfstate
  Operation: OperationTypeApply
  Who:       alice@devops-server
  Version:   1.5.0
  Created:   2026-03-27 10:30:00.123456 +0000 UTC
```

你可以直接查詢 DynamoDB 確認鎖定狀態：

```bash
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "my-terraform-state/prod/infrastructure.tfstate"}}' \
  --region ap-northeast-1
```

如果查詢結果顯示鎖定時間已超過合理範圍（例如數小時前），且確認該同事已經不在操作中，這就是需要處理的幽靈鎖。

## 安全解除鎖定的標準流程

強制解鎖是危險操作，務必遵循以下步驟：

**步驟一：確認無人正在操作**

透過團隊溝通管道（Slack、Teams）確認 Lock Info 中顯示的使用者確實已停止操作。

**步驟二：執行強制解鎖**

```bash
terraform force-unlock a1b2c3d4-5678-90ab-cdef-example12345
```

系統會要求你輸入 `yes` 確認。如果要在自動化腳本中使用，可加上 `-force` 參數：

```bash
terraform force-unlock -force a1b2c3d4-5678-90ab-cdef-example12345
```

**步驟三：驗證 state 完整性**

解鎖後立即執行 `terraform plan`，確認 state 沒有損壞且基礎設施狀態正確。

## 預防勝於治療：團隊協作最佳實踐

建立完善的流程比事後處理更重要。以下是經過驗證的實踐方式：

**導入 CI/CD 集中執行**

將 Terraform 操作收斂到 CI/CD pipeline，避免多人同時在本機執行：

```yaml
# GitLab CI 範例
terraform_apply:
  stage: deploy
  script:
    - terraform init
    - terraform apply -auto-approve
  resource_group: terraform-prod  # 確保同一環境只有一個 job 執行
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

**設定合理的鎖定超時**

在 backend 配置中加入超時設定，避免無限等待：

```hcl
terraform {
  backend "s3" {
    # ... 其他配置
    skip_metadata_api_check = false
  }
}
```

執行時可指定超時：

```bash
terraform apply -lock-timeout=5m
```

## 結論與行動建議

State lock 機制是 Terraform 多人協作的基石，理解其運作原理能幫助你快速排除問題。建議你的團隊採取以下行動：

1. **今天就做**：確認 DynamoDB lock table 已正確配置並有適當的備份
2. **本週完成**：建立團隊的 Terraform 操作規範，包含解鎖的 SOP
3. **長期規劃**：將 Terraform 操作遷移至 CI/CD pipeline，從根本減少衝突機會

記住，`force-unlock` 是最後手段，良好的協作流程才是根本解方。

---
date: 2026-03-27
topic: Terraform
tags: [devops, terraform, state-management, infrastructure-as-code, team-collaboration]
---