(function () {
  const normalizar = (valor) => {
    let texto = String(valor || "").trim();
    if (!texto.startsWith("#")) texto = `#${texto}`;
    return /^#[0-9A-Fa-f]{6}$/.test(texto) ? texto.toUpperCase() : "";
  };

  const enlazar = (caja) => {
    const picker = caja.querySelector(".color-paleta-picker");
    const hex = caja.querySelector(".color-paleta-hex");
    const muestra = caja.querySelector(".color-paleta-muestra");
    if (!picker || !hex || !muestra) return;

    const pintar = (valor) => {
      const color = normalizar(valor);
      if (!color) return;
      picker.value = color;
      hex.value = color;
      muestra.style.background = color;
    };

    picker.addEventListener("input", () => pintar(picker.value));
    hex.addEventListener("input", () => pintar(hex.value));
    hex.addEventListener("blur", () => pintar(hex.value || picker.value));
    caja.querySelectorAll(".color-paleta-swatch").forEach((boton) => {
      boton.addEventListener("click", () => pintar(boton.dataset.color));
    });
  };

  document.querySelectorAll("[data-color-paleta]").forEach(enlazar);
})();
