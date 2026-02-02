fetch("/components/backend.html")
  .then(res => res.text())
  .then(html => {
    const slot = document.getElementById("intro-backend-slot");
    slot.innerHTML = html;

    // ⭐ 一定要在這裡找！
    const introTextContainer2 =
      document.getElementById("intro-backend-container");

    console.log(introTextContainer2); // OK
    initSportAccordion();
  });


    fetch("/components/sport.html")
  .then(res => res.text())
  .then(html => {
    const slot = document.getElementById("intro-sport-slot");
    slot.innerHTML = html;

    // ⭐ 一定要在這裡找！
    const introTextContainer2 =
      document.getElementById("intro-text-container2");

    console.log(introTextContainer2); // OK
    initSportAccordion();
  });
  
    function initSportAccordion() {
      document.querySelectorAll(".sport-header").forEach(header => {
        header.addEventListener("click", () => {
          const group = header.parentElement;

          document.querySelectorAll(".sport-group").forEach(g => {
            if (g !== group) g.classList.remove("active");
          });

          group.classList.toggle("active");
        });
      });
    }