(function () {
  const A4_W = 21;
  const hoja = document.getElementById("hoja");
  if (!hoja) return;

  const ctx = JSON.parse(document.getElementById("ctx-json").textContent);
  const layout = JSON.parse(document.getElementById("layout-json").textContent);
  const layoutDefault = JSON.parse(document.getElementById("layout-default-json").textContent);
  const layoutInput = document.getElementById("layout_json");
  const tituloProp = document.getElementById("prop-titulo");
  const nombres = {
    pagina: "Hoja",
    encabezado: "Encabezado",
    logo: "Logo",
    titulo: "Título",
    cuerpo: "Cuerpo",
    caja: "Caja de datos",
    qr: "Código QR",
    verificacion: "Verificación",
    pie: "Pie de página",
  };
  const sel = {
    x: document.getElementById("sel_x"),
    y: document.getElementById("sel_y"),
    w: document.getElementById("sel_w"),
    h: document.getElementById("sel_h"),
    font: document.getElementById("sel_font"),
    fit: document.getElementById("sel_fit"),
    color: document.getElementById("sel_color"),
    bg: document.getElementById("sel_bg"),
    bgOn: document.getElementById("sel_bg_on"),
    zoom: document.getElementById("sel_zoom"),
    panx: document.getElementById("sel_panx"),
    pany: document.getElementById("sel_pany"),
  };
  const pageBg = document.getElementById("page_bg");

  let activo = "titulo";
  const cmToPx = () => hoja.clientWidth / A4_W;
  const redondear = (n) => Math.round((Number(n) || 0) * 100) / 100;
  const cm = (n) => redondear(n).toFixed(2);
  const hex = (valor, fallback) => (/^#[0-9A-Fa-f]{6}$/.test(valor || "") ? valor : fallback);

  const persistir = () => {
    Object.keys(layout).forEach((clave) => {
      const box = layout[clave];
      if (!box || clave === "pagina") return;
      ["x", "y", "w", "h"].forEach((k) => {
        if (k in box) box[k] = redondear(box[k]);
      });
    });
    layoutInput.value = JSON.stringify(layout);
  };

  const bloquesHoja = () => hoja.querySelectorAll("[data-bloque]");

  const aplicar = () => {
    const k = cmToPx();
    hoja.style.background = hex(layout.pagina?.bg, "#FFFFFF");
    bloquesHoja().forEach((el) => {
      const box = layout[el.dataset.bloque];
      if (!box) return;
      el.style.left = `${box.x * k}px`;
      el.style.top = `${box.y * k}px`;
      el.style.width = `${box.w * k}px`;
      el.style.height = `${box.h * k}px`;
      el.style.zIndex = String(20 + Number(box.z || 0));
      el.style.background = box.bg || "transparent";
      el.style.borderRadius = `${(Number(box.radius) || 0) * k}px`;
      el.style.color = hex(box.color, "#1F2A1F");
      const pad = Number(box.pad ?? 0.15);
      const padL = Number(box.padL ?? pad);
      const contenido = el.querySelector(".bloque-contenido");
      const texto = el.querySelector(".bloque-texto");
      if (contenido && !contenido.classList.contains("crop") && !contenido.classList.contains("qr-ph")) {
        contenido.style.top = `${pad * k}px`;
        contenido.style.right = `${pad * k}px`;
        contenido.style.bottom = `${pad * k}px`;
        contenido.style.left = `${padL * k}px`;
        contenido.style.textAlign = box.align || "left";
      }
      if (texto) {
        const ptAPx = (pt) => Math.max(8, pt * (2.54 / 72) * k);
        let pt = Number(box.font) || 12;
        texto.style.fontSize = `${ptAPx(pt)}px`;
        texto.style.textAlign = box.align || "left";
        texto.style.color = hex(box.color, "#1F2A1F");
        texto.style.textAlignLast = box.align === "justify" ? "left" : "auto";
        if (box.fit && contenido) {
          while (pt > 7 && texto.scrollHeight > contenido.clientHeight + 2) {
            pt -= 0.5;
            texto.style.fontSize = `${ptAPx(pt)}px`;
          }
        }
      }
      const img = el.querySelector("img");
      if (img) {
        const zoom = Number(box.zoom) || 1;
        const panX = Number(box.panX) || 0;
        const panY = Number(box.panY) || 0;
        img.style.objectFit = "cover";
        img.style.transform = `scale(${zoom}) translate(${panX * 18}%, ${panY * 18}%)`;
      }
    });
    persistir();
    pintarSeleccion();
    ordenarLista();
  };

  const ordenarLista = () => {
    const nav = document.getElementById("lista-capas");
    if (!nav) return;
    const filas = [...nav.querySelectorAll(".capa-fila")];
    const pagina = filas.find((f) => f.querySelector('[data-bloque="pagina"]'));
    const otras = filas.filter((f) => f !== pagina);
    otras.sort((a, b) => {
      const ka = a.querySelector(".capa")?.dataset.bloque;
      const kb = b.querySelector(".capa")?.dataset.bloque;
      return Number(layout[ka]?.z || 0) - Number(layout[kb]?.z || 0);
    });
    if (pagina) nav.appendChild(pagina);
    otras.forEach((fila) => nav.appendChild(fila));
  };

  const mostrarInspector = () => {
    const esPagina = activo === "pagina";
    const esLogo = activo === "logo";
    document.querySelectorAll("[data-show]").forEach((sec) => {
      const tipo = sec.dataset.show;
      sec.hidden =
        (tipo === "pagina" && !esPagina) ||
        (tipo === "bloque" && esPagina) ||
        (tipo === "fondo" && esPagina) ||
        (tipo === "texto" && (esPagina || esLogo || activo === "qr")) ||
        (tipo === "logo" && !esLogo);
    });
  };

  const pintarSeleccion = () => {
    bloquesHoja().forEach((el) => {
      el.classList.toggle("is-active", el.dataset.bloque === activo);
    });
    document.querySelectorAll(".capa").forEach((btn) => {
      btn.classList.toggle("is-on", btn.dataset.bloque === activo);
    });
    if (tituloProp) tituloProp.textContent = nombres[activo] || activo;
    mostrarInspector();
    if (pageBg) pageBg.value = hex(layout.pagina?.bg, "#FFFFFF");
    const box = layout[activo];
    if (!box) return;
    if (sel.x) sel.x.value = cm(box.x);
    if (sel.y) sel.y.value = cm(box.y);
    if (sel.w) sel.w.value = cm(box.w);
    if (sel.h) sel.h.value = cm(box.h);
    if (sel.font) sel.font.value = box.font || 12;
    if (sel.fit) sel.fit.checked = box.fit !== false;
    if (sel.color) sel.color.value = hex(box.color, "#1F2A1F");
    if (sel.bgOn) sel.bgOn.checked = Boolean(box.bg);
    if (sel.bg) sel.bg.value = hex(box.bg, "#FFFFFF");
    if (sel.zoom) sel.zoom.value = box.zoom || 1;
    if (sel.panx) sel.panx.value = box.panX || 0;
    if (sel.pany) sel.pany.value = box.panY || 0;
    document.querySelectorAll("#alineacion button").forEach((btn) => {
      btn.classList.toggle("is-on", btn.dataset.align === (box.align || "left"));
    });
  };

  const elegir = (clave) => {
    activo = clave;
    aplicar();
  };

  const restablecer = (clave) => {
    if (clave === "pagina" || clave === "hoja") {
      layout.pagina = { ...layoutDefault.pagina };
    } else if (layoutDefault[clave]) {
      layout[clave] = { ...layoutDefault[clave] };
    }
    elegir(clave === "hoja" ? "pagina" : clave);
  };

  const actualizarCaja = (cambios) => {
    if (activo === "pagina") {
      layout.pagina = { ...(layout.pagina || {}), ...cambios };
      aplicar();
      return;
    }
    if (!layout[activo]) return;
    layout[activo] = { ...layout[activo], ...cambios };
    aplicar();
  };

  const capasNumericas = () =>
    Object.entries(layout)
      .filter(([k, v]) => k !== "pagina" && v && typeof v === "object")
      .map(([, v]) => Number(v.z || 0));

  document.getElementById("btn-delante")?.addEventListener("click", () => {
    if (!layout[activo]) return;
    actualizarCaja({ z: Math.max(...capasNumericas(), 0) + 1 });
  });
  document.getElementById("btn-atras")?.addEventListener("click", () => {
    if (!layout[activo]) return;
    actualizarCaja({ z: Math.min(...capasNumericas(), 0) - 1 });
  });

  ["x", "y", "w", "h"].forEach((k) => {
    sel[k]?.addEventListener("change", () => {
      actualizarCaja({
        x: redondear(sel.x.value),
        y: redondear(sel.y.value),
        w: redondear(sel.w.value),
        h: redondear(sel.h.value),
      });
    });
  });
  sel.font?.addEventListener("input", () => actualizarCaja({ font: Number(sel.font.value) }));
  sel.fit?.addEventListener("change", () => actualizarCaja({ fit: Boolean(sel.fit.checked) }));
  sel.color?.addEventListener("input", () => actualizarCaja({ color: sel.color.value }));
  sel.bgOn?.addEventListener("change", () => {
    actualizarCaja({ bg: sel.bgOn.checked ? hex(sel.bg?.value, "#FFFFFF") : "" });
  });
  sel.bg?.addEventListener("input", () => {
    if (sel.bgOn && !sel.bgOn.checked) sel.bgOn.checked = true;
    actualizarCaja({ bg: sel.bg.value });
  });
  sel.zoom?.addEventListener("input", () => actualizarCaja({ zoom: Number(sel.zoom.value) }));
  sel.panx?.addEventListener("input", () => actualizarCaja({ panX: Number(sel.panx.value) }));
  sel.pany?.addEventListener("input", () => actualizarCaja({ panY: Number(sel.pany.value) }));
  pageBg?.addEventListener("input", () => actualizarCaja({ bg: pageBg.value }));

  document.querySelectorAll("#alineacion button").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!layout[activo]) return;
      layout[activo].align = btn.dataset.align;
      aplicar();
    });
  });

  document.getElementById("btn-reset-uno")?.addEventListener("click", () => restablecer(activo));
  document.querySelectorAll("[data-reset]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      restablecer(btn.dataset.reset);
    });
  });
  document.querySelectorAll(".capa").forEach((btn) => {
    btn.addEventListener("click", () => elegir(btn.dataset.bloque));
  });
  document.getElementById("btn-preview")?.addEventListener("click", () => {
    hoja.classList.toggle("is-preview");
    const btn = document.getElementById("btn-preview");
    if (btn) btn.textContent = hoja.classList.contains("is-preview") ? "Editar" : "Vista limpia";
  });

  const sustituir = (plantilla) => {
    let texto = plantilla || "";
    Object.keys(ctx)
      .sort((a, b) => b.length - a.length)
      .forEach((clave) => {
        texto = texto.split(`<<${clave}>>`).join(ctx[clave]);
      });
    return texto;
  };

  const setTexto = (id, valor) => {
    const nodo = document.getElementById(id)?.querySelector(".bloque-texto");
    if (nodo) nodo.textContent = valor;
  };

  const refrescarTextos = () => {
    setTexto("preview-titulo", document.getElementById("titulo").value);
    setTexto("preview-cuerpo", sustituir(document.getElementById("cuerpo").value));
    setTexto("preview-verif", sustituir(document.getElementById("texto_verificacion").value));
    setTexto("preview-pie", sustituir(document.getElementById("texto_pie").value));
    aplicar();
  };

  ["titulo", "cuerpo", "texto_verificacion", "texto_pie"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", refrescarTextos);
  });

  document.getElementById("mostrar_logo")?.addEventListener("change", (e) => {
    document.querySelector('[data-bloque="logo"]')?.classList.toggle("is-hidden", !e.target.checked);
  });
  document.getElementById("mostrar_caja_datos")?.addEventListener("change", (e) => {
    document.querySelector('[data-bloque="caja"]')?.classList.toggle("is-hidden", !e.target.checked);
  });
  document.getElementById("mostrar_qr")?.addEventListener("change", (e) => {
    document.querySelector('[data-bloque="qr"]')?.classList.toggle("is-hidden", !e.target.checked);
  });
  document.querySelectorAll("[data-dato]").forEach((input) => {
    input.addEventListener("change", () => {
      document.querySelector(`.dato-${input.dataset.dato}`)?.classList.toggle("is-hidden", !input.checked);
    });
  });

  let modo = null;
  let actual = null;
  let startX = 0;
  let startY = 0;
  let startLeft = 0;
  let startTop = 0;
  let startW = 0;
  let startH = 0;

  const enHoja = (el, nx, ny, nw, nh) => {
    const maxL = hoja.clientWidth - nw;
    const maxT = hoja.clientHeight - nh;
    el.style.left = `${Math.max(0, Math.min(maxL, nx))}px`;
    el.style.top = `${Math.max(0, Math.min(maxT, ny))}px`;
    el.style.width = `${Math.max(20, nw)}px`;
    el.style.height = `${Math.max(20, nh)}px`;
  };

  const syncDesdeEl = (el) => {
    const k = cmToPx();
    const clave = el.dataset.bloque;
    layout[clave] = {
      ...layout[clave],
      x: redondear(el.offsetLeft / k),
      y: redondear(el.offsetTop / k),
      w: redondear(el.offsetWidth / k),
      h: redondear(el.offsetHeight / k),
    };
    persistir();
    pintarSeleccion();
  };

  hoja.addEventListener("pointerdown", (event) => {
    if (hoja.classList.contains("is-preview")) return;
    const handle = event.target.closest(".resize-handle");
    const bloque = event.target.closest("[data-bloque]");
    if (!bloque) {
      elegir("pagina");
      return;
    }
    event.preventDefault();
    activo = bloque.dataset.bloque;
    actual = bloque;
    modo = handle ? "resize" : "drag";
    bloque.classList.add("is-dragging");
    bloque.style.zIndex = "400";
    bloque.setPointerCapture(event.pointerId);
    startX = event.clientX;
    startY = event.clientY;
    startLeft = bloque.offsetLeft;
    startTop = bloque.offsetTop;
    startW = bloque.offsetWidth;
    startH = bloque.offsetHeight;
    pintarSeleccion();
  });

  window.addEventListener("pointermove", (event) => {
    if (!modo || !actual) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    if (modo === "drag") {
      enHoja(actual, startLeft + dx, startTop + dy, startW, startH);
    } else {
      enHoja(actual, startLeft, startTop, startW + dx, startH + dy);
    }
  });

  window.addEventListener("pointerup", () => {
    if (!actual) return;
    actual.classList.remove("is-dragging");
    syncDesdeEl(actual);
    modo = null;
    actual = null;
    aplicar();
  });

  window.addEventListener("resize", aplicar);
  document.getElementById("form-diseno")?.addEventListener("submit", persistir);

  aplicar();
})();
