from io import BytesIO

import qrcode
from django.conf import settings
from django.utils import timezone
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def construir_pdf(certificado) -> bytes:
    junta = certificado.junta
    vecino = certificado.vecino
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    primario = HexColor(junta.color_primario or "#2D8A4E")
    acento = HexColor(junta.color_acento or "#F4C430")
    texto = HexColor("#1F2A1F")

    pdf.setFillColor(primario)
    pdf.rect(0, alto - 3.4 * cm, ancho, 3.4 * cm, fill=1, stroke=0)
    pdf.setFillColor(acento)
    pdf.rect(0, alto - 3.6 * cm, ancho, 0.2 * cm, fill=1, stroke=0)

    pdf.setFillColor(white)
    pdf.setFont("Times-Bold", 16)
    pdf.drawString(2 * cm, alto - 1.6 * cm, junta.nombre.upper())
    pdf.setFont("Times-Roman", 11)
    lugar = " · ".join(p for p in [junta.direccion, junta.comuna] if p)
    pdf.drawString(2 * cm, alto - 2.3 * cm, lugar or "Junta de vecinos")
    pdf.setFont("Times-Bold", 13)
    pdf.drawRightString(ancho - 2 * cm, alto - 1.8 * cm, "Certificado de residencia")

    pdf.setFillColor(texto)
    pdf.setFont("Times-Bold", 18)
    pdf.drawCentredString(ancho / 2, alto - 5.1 * cm, "CERTIFICADO DE RESIDENCIA")

    emitido = timezone.localtime(certificado.emitido_en)
    meses = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    fecha = f"{emitido.day} de {meses[emitido.month - 1]} de {emitido.year}"
    cuerpo = (
        f"La {junta.nombre} certifica que {vecino.nombre_completo}, "
        f"RUT {vecino.rut}, reside en {vecino.direccion}"
        + (f", {junta.comuna}" if junta.comuna else "")
        + f", y se encuentra registrado(a) como vecino(a) vigente de esta organización."
    )
    if junta.presidente:
        cuerpo += f" El presente documento es emitido a solicitud del interesado, bajo la presidencia de {junta.presidente}."

    pdf.setFont("Times-Roman", 12)
    _texto_justificado(pdf, cuerpo, 2.2 * cm, alto - 6.4 * cm, ancho - 4.4 * cm, 16)

    y = alto - 11.2 * cm
    pdf.setFillColor(HexColor("#FFF8EE"))
    pdf.roundRect(2 * cm, y - 3.6 * cm, ancho - 4 * cm, 4.2 * cm, 8, fill=1, stroke=0)
    pdf.setFillColor(texto)
    pdf.setFont("Times-Bold", 11)
    pdf.drawString(2.4 * cm, y, "Datos del vecino")
    pdf.setFont("Times-Roman", 11)
    lineas = [
        f"Nombre: {vecino.nombre_completo}",
        f"RUT: {vecino.rut}",
        f"Domicilio: {vecino.direccion}",
        f"Fecha de emisión: {fecha}",
        f"Código de verificación: {certificado.codigo}",
    ]
    for i, linea in enumerate(lineas):
        pdf.drawString(2.4 * cm, y - 0.55 * cm * (i + 1), linea)

    qr_url = f"{settings.SITE_URL}/verificar/{certificado.codigo}/"
    qr_img = qrcode.make(qr_url)
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    pdf.drawImage(ImageReader(qr_buf), ancho - 6.1 * cm, y - 3.3 * cm, 3.2 * cm, 3.2 * cm, mask="auto")

    pdf.setFont("Times-Roman", 9)
    pdf.setFillColor(HexColor("#3A4A3A"))
    aviso = (
        "Este documento puede verificarse en el sitio web de la junta escaneando el código QR "
        "o ingresando el código. Si el PDF fue alterado, el verificador mostrará los datos oficiales."
    )
    _texto_justificado(pdf, aviso, 2.2 * cm, 4.4 * cm, ancho - 4.4 * cm, 12)

    pdf.setFillColor(primario)
    pdf.rect(0, 0, ancho, 1.6 * cm, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("Times-Roman", 9)
    pdf.drawCentredString(ancho / 2, 0.75 * cm, f"Huella: {certificado.contenido_hash[:16]} · {qr_url}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _texto_justificado(pdf, texto, x, y, ancho_max, leading):
    palabras = texto.split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if pdf.stringWidth(prueba, "Times-Roman", 12 if leading > 13 else 9) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    for i, linea in enumerate(lineas):
        pdf.drawString(x, y - i * leading, linea)
