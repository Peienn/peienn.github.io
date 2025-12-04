const postList = document.getElementById('post-list');

// 分類名稱和圖示對應
const categoryInfo = {
  tech: { name: '💻 技術筆記', icon: 'fas fa-code' },
  life: { name: '☕ 日常生活', icon: 'fas fa-coffee' },
  sport: { name: '🏃 運動健身', icon: 'fas fa-running' },
  travel: { name: '✈️ 旅遊紀錄', icon: 'fas fa-plane' }
};

// 載入文章
fetch('posts/posts.json')
  .then(res => res.json())
  .then(posts => {
    // 生成文章卡片
    postList.innerHTML = posts.map(post => {
      const category = post.category || 'tech';
      const categoryName = categoryInfo[category]?.name || category;
      const excerpt = post.excerpt || '';
      
      return `
        <article class="article-card" data-category="${category}">
          <span class="article-category ${category}">${categoryName}</span>
          <h3>
            <a href="posts/templates.html?file=posts/${post.file}" style="text-decoration: none; color: inherit;">
              ${post.title}
            </a>
          </h3>
          <div class="date">📅 ${post.date}</div>
          ${excerpt ? `<div class="excerpt">${excerpt}</div>` : ''}
        </article>
      `;
    }).join('');

    // 更新分類統計數量
    updateCategoryStats(posts);
  })
  .catch(err => {
    console.error(err);
    postList.innerHTML = '<p>❌ 文章清單載入失敗。</p>';
  });

// 更新分類統計
function updateCategoryStats(posts) {
  const counts = {};
  
  // 計算每個分類的文章數量
  posts.forEach(post => {
    const category = post.category || 'tech';
    counts[category] = (counts[category] || 0) + 1;
  });
  
  // 更新顯示
  Object.keys(counts).forEach(category => {
    const countElement = document.querySelector(`[data-category-count="${category}"]`);
    if (countElement) {
      countElement.textContent = counts[category];
    }
  });
  
  // 隱藏數量為 0 的分類
  Object.keys(categoryInfo).forEach(category => {
    if (!counts[category]) {
      const countElement = document.querySelector(`[data-category-count="${category}"]`);
      if (countElement) {
        countElement.textContent = '0';
        countElement.parentElement.style.opacity = '0.5';
      }
    }
  });
}

// 分類篩選功能
document.addEventListener('DOMContentLoaded', function() {
  const categoryBtns = document.querySelectorAll('.category-btn');
  const introTextContainer = document.getElementById('intro-text-container');
  
  function filterCategory(category) {
    const articles = document.querySelectorAll('.article-card');
    
    articles.forEach(article => {
      if (category === 'all' || article.dataset.category === category) {
        article.classList.remove('hidden');
      } else {
        article.classList.add('hidden');
      }
    });

    if (category === 'tech') {
      introTextContainer.style.display = 'block';
    } else {
      introTextContainer.style.display = 'none';
    }
  }

  categoryBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      categoryBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const category = this.dataset.category;
      filterCategory(category);
    });
  });

  // 頁面載入時，依預設的 active 按鈕執行一次篩選與顯示控制
  const activeBtn = document.querySelector('.category-btn.active');
  if (activeBtn) {
    filterCategory(activeBtn.dataset.category);
  } else {
    // 沒有預設 active 的話，隱藏 introTextContainer
    introTextContainer.style.display = 'none';
  }
});
