  // Dark mode
  const darkBtn = document.getElementById('darkToggle');
  darkBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark');  // 切換 dark 類別
  
    // 更新按鈕文字
    if(document.body.classList.contains('dark')){
      darkBtn.textContent = '☀️ 日間模式';
    } else {
      darkBtn.textContent = '🌙 夜間模式';
    }
  });