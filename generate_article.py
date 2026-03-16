#!/usr/bin/env python3
"""
DevOps 文章自動生成器
每天自動呼叫 Claude API 產生一篇 DevOps 技術文章，並儲存為 Markdown 檔案
"""

import anthropic
import random
import os
from datetime import datetime

# ── 主題池：每天從這裡隨機選一個 ──────────────────────────────────────
TOPICS = [
    # ── SRE ──────────────────────────────────────────────────────
    "SLO / SLI / Error Budget：如何定義與追蹤服務可靠性",
    "On-Call 文化建立：Runbook 撰寫與事故回應流程",
    "Post-Mortem 撰寫指南：從事故中學習而不究責",
    "Chaos Engineering 實戰：用 Chaos Monkey 主動找出系統弱點",
    "Capacity Planning：預測流量與資源規劃方法論",
    "分散式系統的可觀測性：Metrics、Logs、Traces 三支柱",
    "Alert 設計原則：減少 Alert Fatigue 的最佳實踐",
    "Toil 識別與消除：SRE 如何釋放工程師的時間",
    "Multi-Region 高可用架構設計與 Failover 策略",
    "服務降級與熔斷器（Circuit Breaker）模式實戰",

    # ── DevOps ───────────────────────────────────────────────────
    "CI/CD Pipeline 最佳實踐：從程式碼提交到自動部署",
    "GitOps 工作流：以 Git 為核心的部署哲學",
    "ArgoCD 實現 Kubernetes GitOps 持續交付",
    "Terraform 進階技巧：Module 設計與 State 管理",
    "Helm Chart 開發與版本管理最佳實踐",
    "DevSecOps：在 CI/CD Pipeline 中嵌入安全掃描",
    "容器安全掃描：Trivy + Harbor 實戰",
    "Ansible 自動化組態管理：從安裝到 Playbook 設計",
    "藍綠部署 vs 金絲雀發布：選型與實作比較",
    "GitHub Actions 進階：可重用 Workflow 與 Matrix Build",
    "Kubernetes 資源管理：Request、Limit 與 HPA 自動擴展",
    "AWS EKS 叢集建置：Node Group、IAM Role 與網路設定",
    "Vault 秘密管理：動態憑證與 Kubernetes 整合",
    "Prometheus + Grafana：從零建立完整監控儀表板",
    "Log 集中管理：ELK Stack vs Loki 選型與部署",
    "Docker 多階段建構：縮小映像大小的實戰技巧",
    "服務網格（Service Mesh）：Istio vs Linkerd 比較",

    # ── Backend Engineer ─────────────────────────────────────────
    "RESTful API 設計原則：版本控制、錯誤處理與分頁",
    "gRPC vs REST：什麼時候該選用 gRPC？",
    "資料庫索引設計：如何分析 Slow Query 並優化",
    "Redis 快取策略：Cache Aside、Write Through 與失效設計",
    "Message Queue 選型：Kafka vs RabbitMQ vs SQS",
    "分散式鎖實作：Redis RedLock 與 ZooKeeper 比較",
    "JWT 與 OAuth 2.0：API 認證授權機制完整解析",
    "資料庫連線池調優：如何避免連線耗盡問題",
    "非同步任務處理：Celery + Redis 實戰架構",
    "API Rate Limiting 實作：Token Bucket 與 Sliding Window",
    "PostgreSQL JSONB vs MongoDB：文件型資料的選型思考",
    "微服務拆分原則：從單體到微服務的漸進式策略",
    "Event-Driven Architecture：CQRS 與 Event Sourcing 入門",
    "後端效能分析：Profiling 工具與瓶頸定位方法",
    "Zero Downtime Deployment：資料庫 Migration 不停機技巧",
]

# ── 設定 ──────────────────────────────────────────────────────────────
LANGUAGE = os.environ.get("ARTICLE_LANG", "zh-TW")       # zh-TW | en | zh-CN
AUDIENCE = os.environ.get("ARTICLE_AUDIENCE", "intermediate")  # beginner | intermediate | senior
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "articles")

LANG_MAP = {"zh-TW": "繁體中文", "en": "英文", "zh-CN": "簡體中文"}
AUDIENCE_MAP = {
    "beginner": "初學者，需要解釋基礎概念",
    "intermediate": "中階 DevOps 工程師，熟悉基本概念",
    "senior": "資深工程師，可深入技術細節與架構決策",
}


def build_prompt(topic: str) -> str:
    lang = LANG_MAP.get(LANGUAGE, "繁體中文")
    audience = AUDIENCE_MAP.get(AUDIENCE, AUDIENCE_MAP["intermediate"])
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""請用{lang}撰寫一篇關於「{topic}」的 DevOps 技術文章。

要求：
- 目標讀者：{audience}
- 長度：約 1000～1200 字
- 格式：標準 Markdown
- 結構：
  1. 吸引人的文章標題（H1）
  2. 前言（說明問題背景與為何重要）
  3. 3～5 個主要段落，每段有 H2 小標題
  4. 每段盡量包含具體指令、工具名稱或程式碼範例（用 code block）
  5. 結論與行動建議
- 在文章最後加上 metadata 區塊：
  ```
  ---
  date: {today}
  topic: {topic}
  tags: [devops, 相關tag1, 相關tag2]
  ---
  ```

請直接輸出 Markdown 內容，不需要任何前言說明。"""


def save_article(content: str, topic: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    # 取主題前20字作為檔名，移除特殊字元
    safe_topic = "".join(c if c.isalnum() or c in "-_ " else "" for c in topic[:20])
    safe_topic = safe_topic.strip().replace(" ", "-")
    filename = f"{today}-{safe_topic}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def generate_article(topic: str | None = None) -> str:
    """產生文章，回傳儲存的檔案路徑"""
    if topic is None:
        topic = random.choice(TOPICS)

    print(f"📝 正在產生文章：{topic}")

    client = anthropic.Anthropic()  # 自動讀取 ANTHROPIC_API_KEY 環境變數

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": build_prompt(topic)}],
    )

    content = message.content[0].text
    filepath = save_article(content, topic)

    print(f"✅ 文章已儲存：{filepath}")
    print(f"📊 Token 使用：input={message.usage.input_tokens}, output={message.usage.output_tokens}")

    return filepath


if __name__ == "__main__":
    import sys
    # 可選：從命令列傳入自訂主題
    custom_topic = sys.argv[1] if len(sys.argv) > 1 else None
    generate_article(custom_topic)
