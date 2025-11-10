async function loadPostList() {
  const listDiv = document.getElementById("post-list");
  listDiv.innerHTML = "<p>載入中...</p>";

  try {
    // GitHub Pages 不允許直接讀取資料夾清單，
    // 所以我們手動維護一份 posts.json（會自動更新版本我可以幫你做，但這版是手動）
    const response = await fetch("posts/posts.json");
    const posts = await response.json();

    listDiv.innerHTML = "";
    posts.forEach(post => {
      const a = document.createElement("a");
      a.textContent = post.title;
      a.href = "#";
      a.onclick = () => loadPost(post.file);
      listDiv.appendChild(a);
      listDiv.appendChild(document.createElement("br"));
    });
  } catch (e) {
    listDiv.innerHTML = "<p>載入文章清單失敗。</p>";
  }
}

async function loadPost(filename) {
  const contentDiv = document.getElementById("content");
  contentDiv.innerHTML = "<p>載入中...</p>";

  const res = await fetch(`posts/${filename}`);
  const text = await res.text();
  contentDiv.textContent = text; // 直接顯示 markdown 原文
}

// 初始化
loadPostList();
