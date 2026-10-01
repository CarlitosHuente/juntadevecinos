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
  if (slides.length) {
    let index = 0;
    const show = (next) => {
      slides[index].classList.remove("is-active");
      index = (next + slides.length) % slides.length;
      slides[index].classList.add("is-active");
    };
    document.querySelector("[data-prev]")?.addEventListener("click", () => show(index - 1));
    document.querySelector("[data-next]")?.addEventListener("click", () => show(index + 1));
    setInterval(() => show(index + 1), 7000);
  }

  const lightbox = document.getElementById("lightbox");
  if (!lightbox) return;
  const foto = lightbox.querySelector("img");
  const pie = lightbox.querySelector(".lightbox-pie");
  document.querySelectorAll("[data-lightbox]").forEach((boton) => {
    boton.addEventListener("click", () => {
      foto.src = boton.dataset.lightbox;
      foto.alt = boton.dataset.caption || "Foto de la actividad";
      pie.textContent = boton.dataset.caption || "";
      lightbox.showModal();
    });
  });
  lightbox.querySelector("[data-lightbox-close]")?.addEventListener("click", () => lightbox.close());
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) lightbox.close();
  });
})();
