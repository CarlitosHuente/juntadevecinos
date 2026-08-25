from io import BytesIO

import qrcode
from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from vecinos.layout import layout_completo, orden_pintado
from vecinos.models import CUERPO_CERTIFICADO_DEFAULT, DisenoCertificado
from vecinos.variables import contexto_certificado, renderizar


def construir_pdf(certificado) -> bytes:
    junta = certificado.junta
    diseno = _diseno(junta)
    layout = layout_completo(diseno)
    ctx = contexto_certificado(certificado)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    pagina_bg = _hex(layout.get("pagina", {}).get("bg") or "#FFFFFF")
    pdf.setFillColor(pagina_bg)
    pdf.rect(0, 0, ancho, alto, fill=1, stroke=0)

    for clave in orden_pintado(layout):
        _dibujar_bloque(pdf, clave, layout[clave], alto, diseno, junta, ctx)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _dibujar_bloque(pdf, clave, caja, alto, diseno, junta, ctx):
    if clave == "logo" and not diseno.mostrar_logo:
        return
    if clave == "caja" and not diseno.mostrar_caja_datos:
        return
    if clave == "qr" and not diseno.mostrar_qr:
        return

    if caja.get("bg"):
        _rect(pdf, caja, alto, _hex(caja["bg"]), radio=caja.get("radius") or 0)

    if clave == "logo":
        logo = diseno.logo if diseno.logo else junta.logo
        if not logo:
            return
        try:
            recorte = _logo_recortado(
                logo.path,
                caja.get("zoom") or 1,
                caja.get("panX") or 0,
                caja.get("panY") or 0,
                caja["w"],
                caja["h"],
            )
            pdf.drawImage(
                ImageReader(recorte),
                caja["x"] * cm,
                alto - (caja["y"] + caja["h"]) * cm,
                caja["w"] * cm,
                caja["h"] * cm,
                mask="auto",
                preserveAspectRatio=True,
                anchor="c",
            )
        except Exception:
            return
        return

    if clave == "qr":
        qr_img = qrcode.make(ctx["url.verificacion"])
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        pad = float(caja.get("pad") or 0)
        pdf.drawImage(
            ImageReader(qr_buf),
            (caja["x"] + pad) * cm,
            alto - (caja["y"] + caja["h"] - pad) * cm,
            max(0.4, caja["w"] - pad * 2) * cm,
            max(0.4, caja["h"] - pad * 2) * cm,
            mask="auto",
        )
        return

    texto, fuente, color = _contenido(clave, caja, diseno, junta, ctx)
    if not texto:
        return
    _texto_en_caja(pdf, texto, caja, alto, fuente, _hex(color))


def _contenido(clave, caja, diseno, junta, ctx):
    color = caja.get("color") or "#1F2A1F"
    if clave == "encabezado":
        lugar = " · ".join(p for p in [junta.direccion, junta.comuna] if p) or "Junta de vecinos"
        return f"{junta.nombre.upper()}\n{lugar}", "Times-Bold", caja.get("color") or "#FFFFFF"
    if clave == "titulo":
        return diseno.titulo or "CERTIFICADO DE RESIDENCIA", "Times-Bold", color
    if clave == "cuerpo":
        return renderizar(diseno.cuerpo or CUERPO_CERTIFICADO_DEFAULT, ctx), "Times-Roman", color
    if clave == "caja":
        lineas = ["Datos del certificado"]
        if diseno.mostrar_nombre:
            lineas.append(f"Nombre: {ctx['nombre']}")
        if diseno.mostrar_rut:
            lineas.append(f"RUT: {ctx['rut']}")
        if diseno.mostrar_domicilio:
            lineas.append(f"Domicilio: {ctx['domicilio']}")
        if diseno.mostrar_fecha:
            lineas.append(f"Fecha de emisión: {ctx['fecha.emision']}")
        if diseno.mostrar_codigo:
            lineas.append(f"Código de verificación: {ctx['codigo']}")
        return "\n".join(lineas), "Times-Roman", color
    if clave == "verificacion":
        return renderizar(diseno.texto_verificacion, ctx), "Times-Roman", caja.get("color") or "#3A4A3A"
    if clave == "pie":
        return renderizar(diseno.texto_pie, ctx), "Times-Roman", caja.get("color") or "#FFFFFF"
    return "", "Times-Roman", color


def _diseno(junta) -> DisenoCertificado:
    diseno = getattr(junta, "diseno_certificado", None)
    if diseno:
        return diseno
    return DisenoCertificado(junta=junta)


def _hex(valor):
    try:
        return HexColor(valor or "#1F2A1F")
    except Exception:
        return white


def _logo_recortado(path, zoom, pan_x, pan_y, box_w, box_h) -> BytesIO:
    imagen = Image.open(path).convert("RGBA")
    iw, ih = imagen.size
    zoom = max(1.0, float(zoom or 1))
    target = float(box_w) / max(0.01, float(box_h))
    if iw / ih > target:
        base_h = float(ih)
        base_w = ih * target
    else:
        base_w = float(iw)
        base_h = iw / target
    recorte_w = base_w / zoom
    recorte_h = base_h / zoom
    max_x = max(0.0, iw - recorte_w)
    max_y = max(0.0, ih - recorte_h)
    cx = max_x / 2 + float(pan_x or 0) * (max_x / 2)
    cy = max_y / 2 + float(pan_y or 0) * (max_y / 2)
    cx = max(0.0, min(max_x, cx))
    cy = max(0.0, min(max_y, cy))
    recorte = imagen.crop((cx, cy, cx + recorte_w, cy + recorte_h))
    buf = BytesIO()
    recorte.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _rect(pdf, caja, alto, color, radio=0):
    pdf.setFillColor(color)
    x = caja["x"] * cm
    y = alto - (caja["y"] + caja["h"]) * cm
    w = caja["w"] * cm
    h = caja["h"] * cm
    r = float(radio or 0) * cm
    if r:
        pdf.roundRect(x, y, w, h, min(r, min(w, h) / 2), fill=1, stroke=0)
    else:
        pdf.rect(x, y, w, h, fill=1, stroke=0)


def _texto_en_caja(pdf, texto, caja, alto, fuente, color):
    align = caja.get("align") or "left"
    pad = float(caja.get("pad") if caja.get("pad") is not None else 0.15)
    pad_l = float(caja.get("padL") if caja.get("padL") is not None else pad)
    pedido = max(7, int(caja.get("font") or 12))
    ancho_max = max(20, (caja["w"] - pad_l - pad) * cm)
    alto_max = max(10, (caja["h"] - pad * 2) * cm)
    tamano = pedido
    if caja.get("fit", True):
        while tamano > 7:
            lineas = _lineas_completas(pdf, texto, fuente, tamano, ancho_max)
            if len(lineas) * (tamano + 3) <= alto_max:
                break
            tamano -= 1
    pdf.setFillColor(color)
    pdf.setFont(fuente, tamano)
    leading = tamano + 3
    x = (caja["x"] + pad_l) * cm
    y = alto - (caja["y"] + pad) * cm - tamano
    y_min = alto - (caja["y"] + caja["h"] - pad) * cm
    lineas = _lineas_completas(pdf, texto, fuente, tamano, ancho_max)
    for i, linea in enumerate(lineas):
        if y < y_min:
            return
        ultima = i == len(lineas) - 1
        _dibujar_linea(pdf, linea, x, y, ancho_max, align, fuente, tamano, ultima)
        y -= leading


def _lineas_completas(pdf, texto, fuente, tamano, ancho_max):
    lineas = []
    for parrafo in (texto or "").split("\n"):
        lineas.extend(_partir(pdf, parrafo, fuente, tamano, ancho_max))
    return lineas


def _dibujar_linea(pdf, linea, x, y, ancho_max, align, fuente, tamano, ultima):
    if align == "center":
        pdf.drawCentredString(x + ancho_max / 2, y, linea)
        return
    if align == "right":
        pdf.drawRightString(x + ancho_max, y, linea)
        return
    if align == "justify" and not ultima and " " in linea.strip():
        palabras = linea.split()
        if len(palabras) > 1:
            anchos = [pdf.stringWidth(p, fuente, tamano) for p in palabras]
            extra = max(0, ancho_max - sum(anchos))
            espacio = extra / (len(palabras) - 1)
            cursor = x
            for i, palabra in enumerate(palabras):
                pdf.drawString(cursor, y, palabra)
                cursor += anchos[i] + espacio
            return
    pdf.drawString(x, y, linea)


def _partir(pdf, texto, fuente, tamano, ancho_max):
    if not texto:
        return [""]
    palabras = texto.split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if pdf.stringWidth(prueba, fuente, tamano) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas or [""]
