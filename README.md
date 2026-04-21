# 個人撰寫文章  &   🤖DevOps 每日文章自動生成器



## 📁 專案結構

```
├── .github/
│   └── workflows/
│       └── daily-devops-article.yml   # GitHub Actions 排程（每天自動產生文章）

├── article_AI/                        # 🤖 AI 自動產文系統
│   ├── generate_article.py            # 文章生成主程式
│   └── update_posts.py                # 更新 posts.json 以利 Github Page 呈現


├── posts/
│   ├── posts.json                     # 前端讀取的文章清單
│   └── markdown/                      # 📝 所有文章（GitHub Pages 讀這裡）
│       ├── 2025-01-01-CICD-Pipeline.md
│       ├── 2025-01-02-Kubernetes.md
│       ├── Oracle.md
│       └── ...

├── index.html                         # 主頁


├── components/                        # 主頁中每個區塊的文字
|   ├── backend.html                        
│   ├── sport.html  
|   └── ... 

├── scrips/                            # 主頁使用的js
|   ├── main.js                        
│   ├── posts.js  
|   └── ... 
|                    
├── css/                               # 主頁使用的 css
│   ├── style.css
│   └── templates.css

└── README.md
```


## 個人撰寫文章

下班時間自行學習、實作後產出的文章


## 🤖DevOps 每日文章自動生成器
使用 Claude API + GitHub Actions，每天自動產生一篇 DevOps 技術文章並存入此 Repo。


# Localhost 啟動
`python -m http.server 5500`