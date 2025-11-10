// 手動設定文章列表 (之後可自動生成)
const posts = [
  { title: "第一篇文章：開始寫作", file: "first-post.md", date: "2025-11-10" },
  { title: "第二篇文章：資料庫學習筆記", file: "second-post.md", date: "2025-11-09" },
];

const postList = document.getElementById('post-list');

postList.innerHTML = posts.map(post => `
  <article class="post">
    <a href="posts/${post.file.replace('.md', '.html')}" class="post-title">${post.title}</a>
    <div class="post-date">${post.date}</div>
  </article>
`).join('');
