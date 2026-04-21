#!/usr/bin/env python3
"""
DevOps 文章自動生成器
每天自動呼叫 Claude API 產生一篇 DevOps 技術文章，並儲存為 Markdown 檔案
"""

import anthropic
import random
import os
from datetime import datetime

# ── 大方向主題池 ──────────────────────────────────────────────────────
TOPICS = [
    # ── SRE ──────────────────────────────────────────────────────
    "SLO / SLI / Error Budget",
    "On-Call 與事故管理",
    "Chaos Engineering",
    "Capacity Planning",
    "系統可觀測性 Observability",
    "Alert 與監控設計",
    "服務降級與熔斷器",

    # ── DevOps ───────────────────────────────────────────────────
    "CI/CD Pipeline",
    "GitOps",
    "ArgoCD",
    "Terraform",
    "Helm",
    "DevSecOps",
    "Ansible",
    "Kubernetes",
    "AWS EKS",
    "Vault 秘密管理",
    "Prometheus & Grafana",
    "ELK Stack / Loki",
    "Docker",
    "Service Mesh",

    # ── Backend ───────────────────────────────────────────────────
    "RESTful API 設計",
    "gRPC",
    "資料庫索引優化",
    "Redis 快取",
    "Message Queue",
    "JWT 與 OAuth 2.0",
    "非同步任務處理",
    "API Rate Limiting",
    "PostgreSQL",
    "MongoDB",
    "微服務架構",
    "Event-Driven Architecture",
    "後端效能分析",

    # ── Database ──────────────────────────────────────────────────
    "Oracle Database",
    "MySQL",
    "PostgreSQL 進階",
    "資料庫備份與還原",
    "資料庫連線池",
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

    return f"""你是一位資深 SRE/ DevOps / Backend 工程師，今天要寫一篇關於「{topic}」的技術文章。

請你先自己決定一個具體的小主題角度（例如：{topic} 的某個常見問題、某個實用技巧、某個工具比較等），
然後以該角度撰寫一篇完整的技術文章。

要求：
- 語言：{lang}
- 目標讀者：{audience}
- 長度：約 1000～1200 字
- 格式：標準 Markdown
- 結構：
  1. 吸引人的文章標題（H1，要具體反映你選的小主題）
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
