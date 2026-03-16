#!/usr/bin/env python3
"""
更新 peienn.github.io 的 posts.json
把新產生的 AI 文章加入到最下面，category 為 AI_Gen
"""

import json
import sys
import os
from datetime import datetime


def extract_title_from_md(md_filepath: str) -> str:
    """從 md 檔案第一行的 H1 標題取得文章標題"""
    with open(md_filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    # 找不到 H1 就用檔名
    return os.path.basename(md_filepath).replace(".md", "")


def extract_excerpt_from_md(md_filepath: str, max_length: int = 100) -> str:
    """從 md 檔案擷取前言作為 excerpt（跳過標題與空行）"""
    with open(md_filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # 跳過標題、空行、metadata
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        # 取第一段有內容的文字
        excerpt = line[:max_length]
        if len(line) > max_length:
            excerpt += "..."
        return excerpt

    return "AI 自動產生的 DevOps 技術文章"


def update_posts_json(posts_json_path: str, md_filename: str, md_filepath: str):
    """讀取 posts.json，在最下面加入新文章，寫回去"""

    # 讀取現有 posts.json
    with open(posts_json_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    # 檢查是否已存在（避免重複新增）
    existing_files = [p.get("file") for p in posts]
    if md_filename in existing_files:
        print(f"⚠️  {md_filename} 已存在於 posts.json，跳過")
        return

    # 取得文章資訊
    title = extract_title_from_md(md_filepath)
    excerpt = extract_excerpt_from_md(md_filepath)
    today = datetime.now().strftime("%Y-%m-%d")

    # 建立新文章物件
    new_post = {
        "title": title,
        "file": md_filename,
        "date": today,
        "category": "AI_Gen",
        "excerpt": excerpt,
    }

    # 加到最下面
    posts.append(new_post)

    # 寫回 posts.json（保留原本縮排格式）
    with open(posts_json_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    print(f"✅ posts.json 已更新，新增：{title}")
    print(f"   file: {md_filename}")
    print(f"   date: {today}")
    print(f"   category: AI_Gen")
    print(f"   excerpt: {excerpt[:60]}...")


if __name__ == "__main__":
    # 參數：posts.json 路徑、md 檔名、md 完整路徑
    if len(sys.argv) != 4:
        print("用法：python update_posts.py <posts.json路徑> <md檔名> <md完整路徑>")
        sys.exit(1)

    posts_json_path = sys.argv[1]  # e.g. peienn.github.io/post/posts.json
    md_filename = sys.argv[2]      # e.g. 2025-01-01-Kubernetes.md
    md_filepath = sys.argv[3]      # e.g. articles/2025-01-01-Kubernetes.md

    update_posts_json(posts_json_path, md_filename, md_filepath)
