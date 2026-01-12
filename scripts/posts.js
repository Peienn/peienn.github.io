const content = document.getElementById('post-content');
const urlParams = new URLSearchParams(window.location.search);
const file = urlParams.get('file');

if (!file) {
  content.innerHTML = '<p>未指定文章。</p>';
} else {
  // ⭐ 這裡加 "../" 才會正確抓到 posts/GitLab.md
  fetch(`../markdown${file}`)
    .then(res => {
      if (!res.ok) throw new Error('載入失敗: ' + res.status);
      return res.text();
    })
    .then(md => {
      const html = marked.parse(md);
      content.innerHTML = html;
      Prism.highlightAll();
    })
    .catch(err => {
      console.error(err);
      content.innerHTML = '<p>⚠️ 無法載入文章。</p>';
    });
}
