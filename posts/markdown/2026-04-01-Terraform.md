# Terraform State 鎖定機制：解決團隊協作中的狀態衝突問題

## 前言

當你的團隊從單人開發 Terraform 進入多人協作階段時，一定會遇到這個經典場景：兩位工程師同時執行 `terraform apply`，結果狀態檔案被覆蓋，基礎設施出現不一致。這不是偶發事件，而是 Terraform 協作的必經之痛。

State 鎖定（State Locking）是解決這個問題的關鍵機制，但許多團隊只是「設定了」卻不真正理解它的運作原理。本文將深入探討 State Locking 的實作細節，幫助你建立更穩健的團隊協作流程。

## 為什麼 State 衝突如此致命

Terraform 的 state 檔案記錄了「Terraform 認知中的基礎設施現狀」。當兩個操作同時進行：

```
工程師 A: terraform apply (新增 EC2)
工程師 B: terraform apply (修改 Security Group)
```

如果沒有鎖定機制，可能發生以下情況：
- A 讀取 state → B 讀取 state → A 寫入 state → B 寫入 state（覆蓋 A 的變更）
- A 新增的 EC2 在 state 中「消失」，但實際資源存在於 AWS
- 下次 plan 時出現 drift，或更糟——Terraform 嘗試刪除「不存在於 state」的資源

這種狀態不一致往往在數天後才被發現，屆時追蹤問題根源將極為困難。

## S3 Backend 的 DynamoDB 鎖定實作

最常見的生產環境配置是 S3 + DynamoDB 組合。DynamoDB 提供強一致性的鎖定機制：

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

建立 DynamoDB Table 時，必須使用 `LockID` 作為 Partition Key：

```hcl
resource "aws_dynamodb_table" "terraform_lock" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Purpose = "Terraform State Locking"
  }
}
```

當 `terraform plan` 或 `apply` 執行時，Terraform 會在 DynamoDB 寫入一筆鎖定記錄，包含操作者資訊與時間戳記。其他操作嘗試取得鎖定時會收到明確的錯誤訊息。

## 處理鎖定異常的實戰技巧

有時候你會遇到殘留鎖定的情況——例如 CI/CD Pipeline 中途被強制終止，鎖定未被正確釋放。

查看當前鎖定狀態：

```bash
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "my-terraform-state/prod/infrastructure.tfstate"}}'
```

如果確認鎖定已經是孤兒狀態（原持有者已不存在），可以強制解鎖：

```bash
terraform force-unlock <LOCK_ID>
```

**重要警告**：在執行 `force-unlock` 之前，務必確認：
1. 沒有其他 apply 正在進行中
2. 與團隊成員確認無人正在操作
3. 檢查 CI/CD Pipeline 是否有正在執行的 Job

盲目解鎖可能導致前面描述的狀態衝突問題。

## 進階：為 CI/CD 設定鎖定超時

在自動化環境中，建議配置合理的鎖定等待時間，而非直接失敗：

```bash
terraform apply -lock-timeout=5m
```

這讓短暫的鎖定衝突可以自動解決，同時避免無限等待。搭配 CI/CD 的整體 timeout 設定，可以建立更健壯的流程：

```yaml
# GitLab CI 範例
terraform_apply:
  script:
    - terraform apply -auto-approve -lock-timeout=5m
  timeout: 30 minutes
  retry:
    max: 2
    when: runner_system_failure
```

## 結論與行動建議

State Locking 不只是一個「該開啟的設定」，而是團隊協作的基礎防護機制。建議你：

1. **立即檢查**：確認現有專案的 backend 是否正確配置 DynamoDB Table
2. **建立規範**：制定 `force-unlock` 的操作 SOP，包含通知機制與確認清單
3. **監控鎖定**：考慮為 DynamoDB Table 設定 CloudWatch 警報，監控異常長時間的鎖定
4. **統一入口**：盡可能將 apply 操作收斂到 CI/CD Pipeline，減少本機直接操作的機會

理解鎖定機制的運作原理，能讓你在遇到問題時快速判斷根因，而非只是重試或繞過。這正是資深工程師與初階工程師的差距所在。

---
date: 2026-04-01
topic: Terraform
tags: [devops, terraform, infrastructure-as-code, aws, state-management]
---