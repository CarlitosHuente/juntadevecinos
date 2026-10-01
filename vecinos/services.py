import hashlib
import secrets
from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone

from vecinos.models import Certificado, DisenoCertificado, Familiar, Vecino
from vecinos.pdf import construir_pdf
from vecinos.rut import normalizar_rut, validar_rut


def emitir_certificado_web(junta, rut: str, ip: str | None) -> tuple[Certificado | None, str | None]:
    if not validar_rut(rut):
        return None, "El RUT ingresado no es válido."

    rut_norm = normalizar_rut(rut)
    vecino = Vecino.objects.filter(junta=junta, rut=rut_norm, activo=True).first()
    if not vecino:
        if Familiar.objects.filter(socio__junta=junta, rut=rut_norm).exists():
            return None, (
                "Ese RUT corresponde a un integrante del grupo familiar. "
                "El certificado lo debe emitir la directiva en la sede."
            )
        return None, "No encontramos un socio titular vigente con ese RUT."

    if not junta.certificado_con_deuda:
        from tesoreria.services import socio_con_deuda

        if socio_con_deuda(vecino):
            return None, "Hay cuotas impagas. Regulariza en la sede para emitir el certificado."

    certificado = crear_certificado(
        junta=junta,
        nombre=vecino.nombre_completo,
        rut=vecino.rut,
        direccion=vecino.direccion,
        vecino=vecino,
        origen=Certificado.Origen.WEB_RUT,
        ip=ip,
    )
    return certificado, None


def crear_certificado(
    *,
    junta,
    nombre: str,
    rut: str,
    direccion: str,
    vecino=None,
    familiar=None,
    origen: str,
    emitido_por=None,
    observacion: str = "",
    ip: str | None = None,
) -> Certificado:
    if not (nombre or "").strip():
        raise ValidationError("El nombre es obligatorio para emitir el certificado.")
    if not (direccion or "").strip():
        raise ValidationError("El domicilio es obligatorio para emitir el certificado.")
    if rut and not validar_rut(rut):
        raise ValidationError("El RUT del certificado no es válido.")

    DisenoCertificado.objects.get_or_create(junta=junta)
    codigo = _nuevo_codigo(junta)
    rut_norm = normalizar_rut(rut) if rut else ""
    certificado = Certificado(
        junta=junta,
        vecino=vecino,
        familiar=familiar,
        nombre_impreso=nombre.strip(),
        rut_impreso=rut_norm,
        direccion_impresa=direccion.strip(),
        origen=origen,
        emitido_por=emitido_por,
        observacion=observacion,
        codigo=codigo,
        contenido_hash="pendiente",
        ip_solicitud=ip,
    )
    certificado.contenido_hash = _huella(certificado)
    certificado.save()
    return certificado


def completar_desde_relaciones(certificado: Certificado) -> None:
    if certificado.familiar_id:
        familiar = certificado.familiar
        certificado.nombre_impreso = certificado.nombre_impreso or familiar.nombre
        certificado.rut_impreso = certificado.rut_impreso or familiar.rut
        if familiar.socio_id:
            certificado.vecino = certificado.vecino or familiar.socio
            certificado.direccion_impresa = certificado.direccion_impresa or familiar.socio.direccion
    elif certificado.vecino_id:
        vecino = certificado.vecino
        certificado.nombre_impreso = certificado.nombre_impreso or vecino.nombre_completo
        certificado.rut_impreso = certificado.rut_impreso or vecino.rut
        certificado.direccion_impresa = certificado.direccion_impresa or vecino.direccion


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


def _huella(certificado: Certificado) -> str:
    base = "|".join(
        [
            str(certificado.junta_id),
            certificado.nombre_impreso,
            certificado.rut_impreso,
            certificado.direccion_impresa,
            certificado.codigo,
            timezone.now().date().isoformat(),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
