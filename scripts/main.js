// the posts list show on index is fetch with  posts/posts.json


fetch('posts/posts.json')
  .then(res => res.json())
  .then(posts => {
    postList.innerHTML = posts.map(post => `
      <article class="post">
        <a href="posts/${post.file.replace('.md', '.html')}" class="post-title">${post.title}</a>
        <div class="post-date">${post.date}</div>
      </article>
    `).join('');
  })
  .catch(err => {
    postList.innerHTML = '<p>文章清單載入失敗。</p>';
    console.error(err);
  });

  
const postList = document.getElementById('post-list');

postList.innerHTML = posts.map(post => `
  <article class="post">
    <a href="posts/${post.file.replace('.md', '.html')}" class="post-title">${post.title}</a>
    <div class="post-date">${post.date}</div>
  </article>
`).join('');
