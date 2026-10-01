from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from tesoreria.layout import layout_completo, orden_pintado
from tesoreria.services import nombre_comprobante, nombre_mes, peso_cl
from tesoreria.variables import (
    CUERPO_COMPROBANTE_DEFAULT,
    PIE_COMPROBANTE_DEFAULT,
    contexto_comprobante,
    renderizar,
)
from vecinos.pdf import _hex, _logo_recortado, _rect, _texto_en_caja


def obtener_diseno(junta):
    from tesoreria.models import DisenoComprobante

    return DisenoComprobante.objects.get_or_create(junta=junta)[0]


def construir_comprobante(vecino, fecha, pagos) -> bytes:
    junta = vecino.junta
    diseno = obtener_diseno(junta)
    layout = layout_completo(diseno)
    ctx = contexto_comprobante(vecino, fecha, pagos)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4
    pdf.setTitle(nombre_comprobante(vecino, fecha).removesuffix(".pdf"))
    pdf.setAuthor(junta.nombre)

    pagina_bg = _hex(layout.get("pagina", {}).get("bg") or "#FFFFFF")
    pdf.setFillColor(pagina_bg)
    pdf.rect(0, 0, ancho, alto, fill=1, stroke=0)

    for clave in orden_pintado(layout):
        _dibujar(pdf, clave, layout[clave], alto, diseno, junta, ctx, pagos)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _dibujar(pdf, clave, caja, alto, diseno, junta, ctx, pagos):
    if clave == "logo" and not diseno.mostrar_logo:
        return
    if clave == "caja" and not diseno.mostrar_caja_datos:
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

    if clave == "detalle":
        _dibujar_detalle(pdf, caja, alto, pagos, caja.get("color") or "#1F2A1F")
        return

    texto, fuente, color = _contenido(clave, caja, diseno, junta, ctx)
    if not texto:
        return
    _texto_en_caja(pdf, texto, caja, alto, fuente, _hex(color))


def _contenido(clave, caja, diseno, junta, ctx):
    color = caja.get("color") or "#1F2A1F"
    if clave == "encabezado":
        lugar = " · ".join(p for p in [junta.direccion, junta.comuna] if p)
        texto = junta.nombre.upper()
        if lugar:
            texto = f"{texto}\n{lugar}"
        return texto, "Helvetica-Bold", caja.get("color") or "#FFFFFF"
    if clave == "titulo":
        return diseno.titulo or "Comprobante de pago", "Helvetica-Bold", color
    if clave == "cuerpo":
        return renderizar(diseno.cuerpo or CUERPO_COMPROBANTE_DEFAULT, ctx), "Helvetica", color
    if clave == "caja":
        lineas = ["Socio titular"]
        if diseno.mostrar_nombre:
            lineas.append(ctx["nombre.socio"])
        if diseno.mostrar_rut:
            lineas.append(f"RUT {ctx['rut.socio']}")
        if diseno.mostrar_domicilio and ctx["domicilio"]:
            lineas.append(ctx["domicilio"])
        if diseno.mostrar_fecha:
            lineas.append(f"Fecha de pago: {ctx['fecha.pago']}")
        return "\n".join(lineas), "Helvetica", color
    if clave == "pie":
        return renderizar(diseno.texto_pie or PIE_COMPROBANTE_DEFAULT, ctx), "Helvetica", caja.get("color") or "#FFFFFF"
    return "", "Helvetica", color


def _dibujar_detalle(pdf, caja, alto, pagos, color):
    x = caja["x"] * cm
    y_top = alto - caja["y"] * cm
    w = caja["w"] * cm
    pad = float(caja.get("pad") or 0.2) * cm
    font = max(9, int(caja.get("font") or 12))
    color_txt = HexColor(color)
    gris = HexColor("#6B7280")
    linea = HexColor("#E5E7EB")
    fondo = HexColor("#F3F4F6")

    y = y_top - pad - font
    pdf.setFillColor(color_txt)
    pdf.setFont("Helvetica-Bold", font)
    pdf.drawString(x + pad, y, "Pagos de este día")
    y -= font + 14

    pdf.setFillColor(fondo)
    pdf.roundRect(x, y - 6, w, font + 16, 4, fill=1, stroke=0)
    pdf.setFillColor(gris)
    pdf.setFont("Helvetica-Bold", max(9, font - 1))
    pdf.drawString(x + pad, y, "Período")
    pdf.drawRightString(x + w - pad, y, "Monto")
    y -= font + 18

    total = 0
    pdf.setFont("Helvetica", font)
    if not pagos:
        pdf.setFillColor(gris)
        pdf.drawString(x + pad, y, "No hay pagos registrados en esta fecha.")
        y -= font + 16
    for pago in pagos:
        y_min = alto - (caja["y"] + caja["h"]) * cm + pad
        if y < y_min + font + 28:
            break
        pdf.setFillColor(color_txt)
        pdf.drawString(x + pad, y, f"{nombre_mes(pago.mes).capitalize()} {pago.anio}")
        pdf.drawRightString(x + w - pad, y, peso_cl(pago.monto))
        total += int(pago.monto)
        y -= font + 16

    y -= 8
    pdf.setStrokeColor(linea)
    pdf.setLineWidth(1)
    pdf.line(x, y + font, x + w, y + font)
    y -= 18
    pdf.setFillColor(color_txt)
    pdf.setFont("Helvetica-Bold", font + 1)
    pdf.drawString(x + pad, y, "Total pagado")
    pdf.drawRightString(x + w - pad, y, peso_cl(total))
