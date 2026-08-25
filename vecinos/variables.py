from types import SimpleNamespace

from django.conf import settings
from django.utils import timezone


def fecha_larga(dt) -> str:
    meses = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    local = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    return f"{local.day} de {meses[local.month - 1]} de {local.year}"


def contexto_certificado(certificado) -> dict[str, str]:
    junta = certificado.junta
    nombre = certificado.nombre_impreso
    rut = certificado.rut_impreso or "—"
    domicilio = certificado.direccion_impresa
    titular = ""
    if certificado.vecino_id:
        titular = certificado.vecino.nombre_completo
    comuna = junta.comuna or ""
    return {
        "nombre": nombre,
        "nombre.socio": nombre,
        "rut": rut,
        "rut.socio": rut,
        "domicilio": domicilio,
        "junta.nombre": junta.nombre,
        "junta.comuna": comuna,
        "junta.direccion": junta.direccion or "",
        "presidente": junta.presidente or "la directiva",
        "fecha.emision": fecha_larga(certificado.emitido_en),
        "codigo": certificado.codigo,
        "socio.titular": titular,
        "comuna.frase": f", {comuna}" if comuna else "",
        "huella": certificado.contenido_hash[:16],
        "url.verificacion": f"{settings.SITE_URL}/verificar/{certificado.codigo}/",
    }


def certificado_muestra(junta):
    return SimpleNamespace(
        junta=junta,
        nombre_impreso="Juan Andrés Pérez Soto",
        rut_impreso="12345678-5",
        direccion_impresa="Pasaje Los Aromos 120",
        codigo="HU-DEMO-PREV",
        contenido_hash="a1b2c3d4e5f6789012345678abcdef01",
        emitido_en=timezone.now(),
        vecino_id=None,
        vecino=None,
    )


def renderizar(plantilla: str, contexto: dict[str, str]) -> str:
    texto = plantilla or ""
    for clave, valor in sorted(contexto.items(), key=lambda item: -len(item[0])):
        texto = texto.replace(f"<<{clave}>>", valor)
    return texto
