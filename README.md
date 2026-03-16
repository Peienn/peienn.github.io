# 🤖 DevOps 每日文章自動生成器

使用 Claude API + GitHub Actions，每天自動產生一篇 DevOps 技術文章並存入此 Repo。

## 📁 專案結構

```
├── generate_article.py              # 文章生成主程式
├── .github/
│   └── workflows/
│       └── daily-devops-article.yml # GitHub Actions 排程設定
├── articles/                        # 自動生成的文章（自動建立）
│   ├── 2025-01-01-CICD-Pipeline.md
│   ├── 2025-01-02-Kubernetes.md
│   └── ...
└── README.md
```

## 🚀 快速開始

### 1. Fork 或 Clone 此 Repo

```bash
git clone https://github.com/YOUR_USERNAME/devops-articles.git
cd devops-articles
```

### 2. 設定 API Key（重要！）

前往 GitHub Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 名稱 | 值 |
|---|---|
| `ANTHROPIC_API_KEY` | 你的 Claude API Key（`sk-ant-...`） |

### 3. 啟用 GitHub Actions

確認 Repo 的 Actions 功能已開啟（Settings → Actions → Allow all actions）。

### 4. 測試手動執行

前往 **Actions** → **每日 DevOps 文章生成** → **Run workflow**

可以輸入自訂主題，或留空讓程式隨機選擇。

---

## ⚙️ 自訂設定

編輯 `.github/workflows/daily-devops-article.yml` 中的環境變數：

| 變數 | 說明 | 選項 |
|---|---|---|
| `ARTICLE_LANG` | 文章語言 | `zh-TW` / `en` / `zh-CN` |
| `ARTICLE_AUDIENCE` | 目標讀者 | `beginner` / `intermediate` / `senior` |
| `OUTPUT_DIR` | 輸出資料夾 | 預設 `articles` |

### 修改排程時間

編輯 `cron` 表達式（UTC 時區）：

```yaml
- cron: "0 0 * * *"   # UTC 00:00 = 台灣時間 08:00
- cron: "0 1 * * *"   # UTC 01:00 = 台灣時間 09:00
- cron: "0 16 * * *"  # UTC 16:00 = 台灣時間 00:00
```

### 新增自訂主題

編輯 `generate_article.py` 的 `TOPICS` 清單，加入你想要的主題。

---

## 💡 進階整合

### 自動發布到 Notion

在 workflow 中加入 Notion API 步驟，將生成的文章同步到 Notion Database。

### 自動發布到 Medium / Dev.to

使用各平台的 API，將文章自動發布到技術部落格。

### 搭配 GitHub Pages

將 `articles/` 資料夾設為 Jekyll 或 Hugo 的來源，自動建立靜態部落格網站。

