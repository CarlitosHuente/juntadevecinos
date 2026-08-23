(function () {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector("#menu-principal");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  const slides = Array.from(document.querySelectorAll("[data-slide]"));
  if (!slides.length) return;

  let index = 0;
  const show = (next) => {
    slides[index].classList.remove("is-active");
    index = (next + slides.length) % slides.length;
    slides[index].classList.add("is-active");
  };

  document.querySelector("[data-prev]")?.addEventListener("click", () => show(index - 1));
  document.querySelector("[data-next]")?.addEventListener("click", () => show(index + 1));
  setInterval(() => show(index + 1), 7000);
})();
