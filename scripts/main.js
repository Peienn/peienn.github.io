const postList = document.getElementById('post-list');

fetch('posts/posts.json')
  .then(res => res.json())
  .then(posts => {
    postList.innerHTML = posts.map(post => `
      <article class="post">
        <a href="posts/templates.html?file=posts/${post.file}" class="post-title">${post.title}</a>
        <div class="post-date">${post.date}</div>
      </article>
    `).join('');
  })
  .catch(err => {
    console.error(err);
    postList.innerHTML = '<p>文章清單載入失敗。</p>';
  });
