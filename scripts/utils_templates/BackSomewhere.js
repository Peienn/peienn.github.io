// 1. Back to Index.html
document.getElementById("index").addEventListener("click", () => {
    window.location.href = "/index.html"; // 回首頁路徑，可依實際調整
  });



  // 2. Back to Top
  const btn = document.getElementById("backToTop");
  // 滾動事件
  window.addEventListener("scroll", () => {
    if(window.scrollY > 200){   // 滾動超過 200px 顯示
      btn.style.display = "block";
    } else {
      btn.style.display = "none";
    }
  });
  btn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
