import hashlib
import secrets
from datetime import date

from django.utils import timezone

from vecinos.models import Certificado, Vecino
from vecinos.pdf import construir_pdf
from vecinos.rut import normalizar_rut, validar_rut


def emitir_certificado(junta, rut: str, ip: str | None) -> tuple[Certificado | None, str | None]:
    if not validar_rut(rut):
        return None, "El RUT ingresado no es válido."

    vecino = Vecino.objects.filter(
        junta=junta,
        rut=normalizar_rut(rut),
        activo=True,
    ).first()
    if not vecino:
        return None, "No encontramos un vecino vigente con ese RUT."

    codigo = _nuevo_codigo(junta)
    certificado = Certificado.objects.create(
        junta=junta,
        vecino=vecino,
        codigo=codigo,
        contenido_hash=_huella(junta, vecino, codigo),
        ip_solicitud=ip,
    )
    return certificado, None


def pdf_de_certificado(certificado: Certificado) -> bytes:
    return construir_pdf(certificado)


def cumple_en_rango(fecha: date | None, hoy: date, dias: int = 7) -> bool:
    if not fecha:
        return False
    try:
        este_anio = fecha.replace(year=hoy.year)
    except ValueError:
        este_anio = fecha.replace(year=hoy.year, day=28)
    delta = (este_anio - hoy).days
    if delta < 0:
        try:
            este_anio = fecha.replace(year=hoy.year + 1)
        except ValueError:
            este_anio = fecha.replace(year=hoy.year + 1, day=28)
        delta = (este_anio - hoy).days
    return 0 <= delta <= dias


def _nuevo_codigo(junta) -> str:
    prefijo = "".join(c for c in junta.slug.upper() if c.isalnum())[:2] or "JV"
    while True:
        codigo = f"{prefijo}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        if not Certificado.objects.filter(codigo=codigo).exists():
            return codigo


def _huella(junta, vecino, codigo: str) -> str:
    base = "|".join(
        [
            str(junta.pk),
            str(vecino.pk),
            vecino.rut,
            vecino.nombre_completo,
            vecino.direccion,
            codigo,
            timezone.now().date().isoformat(),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
