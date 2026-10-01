(function () {
  const parseRatio = (texto) => {
    const partes = String(texto || "16/10").split("/");
    const w = Number(partes[0]) || 16;
    const h = Number(partes[1]) || 10;
    return w / h;
  };
  const limitar = (valor, min, max) => Math.min(max, Math.max(min, valor));

  const armar = (widget) => {
    if (widget.dataset.recorteListo) return;
    const input = widget.querySelector('input[type="file"]');
    const caja = widget.querySelector(".recorte-caja");
    const vista = widget.querySelector(".recorte-vista");
    const marco = widget.querySelector(".recorte-marco");
    const foto = widget.querySelector(".recorte-foto");
    const zoomEl = widget.querySelector(".recorte-zoom");
    const controles = widget.querySelector(".recorte-controles");
    if (!input || !caja || !vista || !marco || !foto || !zoomEl || !controles) return;
    widget.dataset.recorteListo = "1";
    const quitar = widget.querySelector(".recorte-quitar-check");
    const ratio = parseRatio(widget.dataset.ratio || input.dataset.ratio);
    const estado = { zoom: 1, x: 0, y: 0, naturalW: 0, naturalH: 0, sucio: false, arrastre: null, editando: false };

    const vacio = () => {
      caja.hidden = false;
      vista.hidden = true;
      marco.classList.remove("is-editando");
      controles.hidden = true;
      estado.editando = false;
    };

    const medidas = () => {
      const fw = marco.clientWidth || 1;
      const fh = fw / ratio;
      marco.style.height = `${fh}px`;
      const cover = Math.max(fw / (estado.naturalW || 1), fh / (estado.naturalH || 1));
      const escala = cover * estado.zoom;
      const dw = estado.naturalW * escala;
      const dh = estado.naturalH * escala;
      const maxX = Math.max(0, (dw - fw) / 2);
      const maxY = Math.max(0, (dh - fh) / 2);
      estado.x = limitar(estado.x, -maxX, maxX);
      estado.y = limitar(estado.y, -maxY, maxY);
      foto.style.width = `${dw}px`;
      foto.style.height = `${dh}px`;
      foto.style.left = `${(fw - dw) / 2 + estado.x}px`;
      foto.style.top = `${(fh - dh) / 2 + estado.y}px`;
      return { fw, fh, escala };
    };

    const mostrar = (src) => {
      if (!src) {
        vacio();
        return;
      }
      foto.onload = () => {
        estado.naturalW = foto.naturalWidth;
        estado.naturalH = foto.naturalHeight;
        caja.hidden = true;
        vista.hidden = false;
        if (quitar) quitar.checked = false;
        medidas();
      };
      foto.src = src;
    };

    const reset = () => {
      estado.zoom = 1;
      estado.x = 0;
      estado.y = 0;
      zoomEl.value = "1";
      medidas();
    };

    const cambiar = widget.querySelector(".recorte-cambiar");
    const borrar = widget.querySelector(".recorte-borrar");
    if (borrar) {
      borrar.addEventListener("click", () => {
        if (quitar) quitar.checked = true;
        input.value = "";
        estado.sucio = false;
        vacio();
      });
    }

    ["dragenter", "dragover"].forEach((ev) => {
      caja.addEventListener(ev, (e) => {
        e.preventDefault();
        caja.classList.add("is-over");
      });
    });
    ["dragleave", "drop"].forEach((ev) => {
      caja.addEventListener(ev, (e) => {
        e.preventDefault();
        caja.classList.remove("is-over");
      });
    });
    caja.addEventListener("drop", (e) => {
      const archivo = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!archivo) return;
      const data = new DataTransfer();
      data.items.add(archivo);
      input.files = data.files;
      input.dispatchEvent(new Event("change"));
    });

    input.addEventListener("change", () => {
      const archivo = input.files && input.files[0];
      estado.sucio = Boolean(archivo);
      reset();
      if (archivo) mostrar(URL.createObjectURL(archivo));
      else if (input.dataset.inicial && !(quitar && quitar.checked)) mostrar(input.dataset.inicial);
      else vacio();
    });

    const editar = (on) => {
      estado.editando = on;
      marco.classList.toggle("is-editando", on);
      controles.hidden = !on;
      if (on) medidas();
    };

    marco.addEventListener("click", () => {
      if (!estado.editando) editar(true);
    });
    widget.querySelector(".recorte-listo").addEventListener("click", () => editar(false));
    widget.querySelector(".recorte-centrar").addEventListener("click", () => {
      reset();
      estado.sucio = true;
    });
    zoomEl.addEventListener("input", () => {
      estado.zoom = Number(zoomEl.value) || 1;
      estado.sucio = true;
      medidas();
    });

    marco.addEventListener("pointerdown", (ev) => {
      if (!estado.editando) return;
      ev.preventDefault();
      estado.arrastre = { x: ev.clientX, y: ev.clientY, ox: estado.x, oy: estado.y };
      marco.classList.add("is-dragging");
      marco.setPointerCapture(ev.pointerId);
    });
    marco.addEventListener("pointermove", (ev) => {
      if (!estado.arrastre) return;
      estado.x = estado.arrastre.ox + (ev.clientX - estado.arrastre.x);
      estado.y = estado.arrastre.oy + (ev.clientY - estado.arrastre.y);
      estado.sucio = true;
      medidas();
    });
    const soltar = () => {
      estado.arrastre = null;
      marco.classList.remove("is-dragging");
    };
    marco.addEventListener("pointerup", soltar);
    marco.addEventListener("pointercancel", soltar);

    const recortar = () => new Promise((resolve) => {
      if (!estado.sucio || !foto.src || vista.hidden || !estado.naturalW) {
        resolve();
        return;
      }
      const { fw, fh, escala } = medidas();
      const srcW = fw / escala;
      const srcH = fh / escala;
      const srcX = (estado.naturalW - srcW) / 2 - estado.x / escala;
      const srcY = (estado.naturalH - srcH) / 2 - estado.y / escala;
      const salidaW = Math.min(1600, Math.round(srcW));
      const lienzo = document.createElement("canvas");
      lienzo.width = Math.max(1, salidaW);
      lienzo.height = Math.max(1, Math.round(salidaW / ratio));
      lienzo.getContext("2d").drawImage(foto, srcX, srcY, srcW, srcH, 0, 0, lienzo.width, lienzo.height);
      lienzo.toBlob((blob) => {
        if (blob) {
          const nombre = (input.files[0] && input.files[0].name) || "imagen-recorte.jpg";
          const archivo = new File([blob], nombre.replace(/\.[^.]+$/, ".jpg"), { type: "image/jpeg" });
          const data = new DataTransfer();
          data.items.add(archivo);
          input.files = data.files;
        }
        resolve();
      }, "image/jpeg", 0.9);
    });

    input.recorteExportar = recortar;
    if (input.form && !input.form.dataset.recorteSubmit) {
      input.form.dataset.recorteSubmit = "1";
      input.form.addEventListener("submit", (ev) => {
        if (input.form.dataset.recorteEnviado === "1") return;
        ev.preventDefault();
        const jobs = [...input.form.querySelectorAll("[data-recorte]")].map((el) => (
          el.recorteExportar ? el.recorteExportar() : Promise.resolve()
        ));
        Promise.all(jobs).then(() => {
          input.form.dataset.recorteEnviado = "1";
          input.form.requestSubmit();
        });
      });
    }

    if (input.dataset.inicial) mostrar(input.dataset.inicial);
    window.addEventListener("resize", () => {
      if (!vista.hidden) medidas();
    });
  };

  const iniciar = (raiz) => {
    (raiz || document).querySelectorAll(".recorte-widget").forEach(armar);
  };
  const arrancar = () => {
    iniciar();
    if (!document.body) return;
    new MutationObserver((muts) => {
      muts.forEach((m) => m.addedNodes.forEach((nodo) => {
        if (nodo.querySelectorAll) iniciar(nodo);
      }));
    }).observe(document.body, { childList: true, subtree: true });
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arrancar);
  } else {
    arrancar();
  }
})();
