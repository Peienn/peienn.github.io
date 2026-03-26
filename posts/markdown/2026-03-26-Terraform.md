# Terraform State 鎖定衝突：多人協作環境下的實戰解決方案

## 前言

當團隊從單人開發 Terraform 轉向多人協作時，最常遇到的痛點之一就是 State 鎖定衝突。你可能曾經看過這樣的錯誤訊息：`Error acquiring the state lock`，然後整個部署流程卡住，團隊成員互相詢問「是誰在跑 Terraform？」

State 鎖定機制本身是為了保護基礎設施一致性而設計的安全機制，但在 CI/CD pipeline 頻繁觸發、多人同時開發的環境下，鎖定衝突會嚴重影響開發效率。本文將深入探討鎖定衝突的成因，並提供幾種實用的解決策略。

## 理解 State Lock 的運作原理

Terraform 在執行 `plan`、`apply`、`destroy` 等會讀寫 State 的操作時，會先嘗試取得鎖定。以 AWS S3 + DynamoDB 作為 Remote Backend 為例，鎖定資訊會寫入 DynamoDB：

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/infrastructure.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

當鎖定成功時，DynamoDB 會記錄一筆包含 `LockID`、執行者資訊、時間戳記的記錄。問題通常發生在以下情境：CI/CD pipeline 執行到一半被強制終止、網路斷線導致 Terraform 未正常釋放鎖定、或是有人在本機執行後直接關閉終端機。

## 診斷鎖定衝突的狀態

當遇到鎖定錯誤時，首先要確認是「真正的並行操作」還是「殘留的孤兒鎖」。錯誤訊息會提供關鍵資訊：

```bash
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        a1b2c3d4-5678-90ab-cdef-1234567890ab
  Path:      prod/infrastructure.tfstate
  Operation: OperationTypeApply
  Who:       runner@github-actions-runner
  Version:   1.7.0
  Created:   2026-03-26 08:30:15.123456 +0000 UTC
```

透過 `Who` 欄位可以判斷是哪個環境或使用者持有鎖定，`Created` 時間則能幫助判斷是否為殘留鎖。若確認是孤兒鎖，可以使用強制解鎖：

```bash
terraform force-unlock a1b2c3d4-5678-90ab-cdef-1234567890ab
```

但請謹慎使用此指令，在解鎖前務必確認沒有其他操作正在進行。

## 預防策略：CI/CD Pipeline 設計

最根本的解決方案是從 Pipeline 架構層面避免衝突。以下是幾個實用技巧：

**使用排隊機制**：在 GitHub Actions 中設定 concurrency group，確保同一環境的部署不會並行執行：

```yaml
concurrency:
  group: terraform-${{ github.ref }}-${{ inputs.environment }}
  cancel-in-progress: false
```

**實作重試邏輯**：在 CI 腳本中加入自動重試機制，處理短暫的鎖定衝突：

```bash
#!/bin/bash
MAX_RETRIES=3
RETRY_DELAY=30

for i in $(seq 1 $MAX_RETRIES); do
  terraform apply -auto-approve && break
  echo "Attempt $i failed, waiting ${RETRY_DELAY}s before retry..."
  sleep $RETRY_DELAY
done
```

**設定合理的 Lock Timeout**：避免鎖定無限期佔用：

```bash
terraform apply -lock-timeout=5m
```

## 進階方案：State 拆分與模組化

當專案規模成長，單一 State 檔案會成為瓶頸。將基礎設施拆分為多個獨立的 State，能大幅降低衝突機率：

```
infrastructure/
├── network/          # VPC, Subnet, Route Table
├── database/         # RDS, ElastiCache
├── application/      # ECS, ALB
└── monitoring/       # CloudWatch, SNS
```

各模組透過 `terraform_remote_state` data source 引用其他 State 的輸出值：

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "prod/network.tfstate"
    region = "ap-northeast-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.private_subnet_id
}
```

## 結論與行動建議

State 鎖定衝突是 Terraform 多人協作的必經之路。建議依照以下優先順序處理：首先在 CI/CD Pipeline 加入 concurrency 控制，這是最低成本的改善；接著評估 State 拆分的可行性，特別是當團隊超過 3 人或基礎設施資源超過 50 個時；最後建立團隊的操作規範，明確定義誰能在什麼情況下執行 `force-unlock`。

記住，鎖定機制存在的目的是保護你的基礎設施，與其視它為障礙，不如透過良好的架構設計讓它成為協作的護欄。

---
date: 2026-03-26
topic: Terraform
tags: [devops, terraform, infrastructure-as-code, state-management, ci-cd]
---