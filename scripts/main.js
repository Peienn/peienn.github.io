// 分類資訊統一管理
const categoryInfo = {
  tech: { name: '💻 後端技術筆記', icon: 'fas fa-code' },
  //life: { name: '☕ 日常生活', icon: 'fas fa-coffee' },
  training: { name: '📖 學習紀錄', icon: 'fas fa-book-open' },
  sport: { name: '🏃 運動健身', icon: 'fas fa-running' }
  //travel: { name: '✈️ 旅遊紀錄', icon: 'fas fa-plane' }
  
};

// 取得 DOM 元素
const categoryFilter = document.getElementById('category-filter');
const postList = document.getElementById('post-list');
const categoryStatsContainer = document.querySelector('.category-stats');
const introTextContainer = document.getElementById('intro-text-container');


document.addEventListener('DOMContentLoaded', function () {

  // 1. 動態產生分類按鈕（含全部）
  let btnsHtml = `<button class="category-btn active" data-category="all"><i class="fas fa-th"></i> 全部</button>`;
  Object.keys(categoryInfo).forEach(cat => {
    const { name, iconClass } = categoryInfo[cat];
    btnsHtml += `<button class="category-btn" data-category="${cat}">
      <i class="${iconClass}"></i> ${name}
    </button>`;
  });
  categoryFilter.innerHTML = btnsHtml;

  // 2. 動態產生側邊分類統計區 HTML 結構
  let statsHtml = '<h3>文章分類</h3>';
  Object.keys(categoryInfo).forEach(cat => {
    const { name, iconClass } = categoryInfo[cat];
    statsHtml += `
      <div class="stat-item">
        <span class="stat-label"><i class="${iconClass}"></i> ${name}</span>
        <span class="stat-count" data-category-count="${cat}">0</span>
      </div>
    `;
  });
  categoryStatsContainer.innerHTML = statsHtml;

  // 3. 載入並渲染文章列表
  fetch('posts/posts.json')
    .then(res => res.json())
    .then(posts => {
      renderPosts(posts);
      updateCategoryStats(posts);
    })
    .catch(err => {
      console.error(err);
      postList.innerHTML = '<p>❌ 文章清單載入失敗。</p>';
    });

  // 4. 篩選按鈕功能
  const categoryBtns = document.querySelectorAll('.category-btn');
  categoryBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      categoryBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const category = this.dataset.category;
      filterPosts(category);
      toggleIntroText(category);
    });
  });

  // 頁面載入時用預設 active 按鈕執行一次篩選（通常是 "全部"）
  const activeBtn = document.querySelector('.category-btn.active');
  if (activeBtn) {
    filterPosts(activeBtn.dataset.category);
    toggleIntroText(activeBtn.dataset.category);
  }

});

// 渲染文章函式
function renderPosts(posts) {
  // 利用 categoryInfo 物件取得分類名稱
  postList.innerHTML = posts.map(post => {
    const category = post.category || 'tech';
    const categoryName = categoryInfo[category]?.name || category;
    const excerpt = post.excerpt || '';

    return `
      <article class="article-card" data-category="${category}">
        <span class="article-category ${category}">${categoryName}</span>
        <h3>
          <a href="posts/templates.html?file=posts/markdown/${post.file}" style="text-decoration: none; color: inherit;">
            ${post.title}
          </a>
        </h3>
        <div class="date">📅 ${post.date}</div>
        ${excerpt ? `<div class="excerpt">${excerpt}</div>` : ''}
      </article>
    `;
  }).join('');
}

// 篩選文章並顯示/隱藏
function filterPosts(category) {
  const articles = document.querySelectorAll('.article-card');
  
  articles.forEach(article => {
    if (category === 'all' || article.dataset.category === category) {
      article.classList.remove('hidden');
    } else {
      article.classList.add('hidden');
    }
  });
}

// 顯示/隱藏介紹文字區塊（只在 tech 時顯示）
function toggleIntroText(category) {
  if (category === 'tech') {
    introTextContainer.style.display = 'block';
  } else {
    introTextContainer.style.display = 'none';
  }
}

// 更新分類統計區
function updateCategoryStats(posts) {
  // 計算數量
  const counts = {};
  posts.forEach(post => {
    const cat = post.category || 'tech';
    counts[cat] = (counts[cat] || 0) + 1;
  });

  // 更新顯示數字
  Object.keys(categoryInfo).forEach(cat => {
    const countElement = document.querySelector(`[data-category-count="${cat}"]`);
    if (countElement) {
      countElement.textContent = counts[cat] || 0;
      if (!counts[cat]) {
        // 數量為 0，降低透明度
        countElement.parentElement.style.opacity = 0.5;
      } else {
        countElement.parentElement.style.opacity = 1;
      }
    }
  });
}
