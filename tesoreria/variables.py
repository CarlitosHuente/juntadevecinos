from tesoreria.services import nombre_mes, peso_cl
from vecinos.rut import normalizar_rut
from vecinos.variables import renderizar

CUERPO_COMPROBANTE_DEFAULT = "Fecha de pago: <<fecha.pago>>"

PIE_COMPROBANTE_DEFAULT = (
    "Documento emitido por tesorería de <<junta.nombre>>.\n"
    "Conserve este comprobante como constancia de pago."
)

AYUDA_COMPROBANTE = (
    "Variables: <<junta.nombre>>, <<nombre.socio>> o <<nombre>>, <<rut.socio>> o <<rut>>, "
    "<<domicilio>>, <<fecha.pago>>, <<total>>, <<presidente>>."
)


def rut_con_puntos(rut: str) -> str:
    limpio = normalizar_rut(rut)
    if "-" not in limpio:
        return limpio
    cuerpo, dv = limpio.split("-")
    grupos = []
    while cuerpo:
        grupos.append(cuerpo[-3:])
        cuerpo = cuerpo[:-3]
    return f"{'.'.join(reversed(grupos))}-{dv}"


def contexto_comprobante(vecino, fecha, pagos) -> dict[str, str]:
    junta = vecino.junta
    total = sum(int(p.monto) for p in pagos)
    lineas = [f"{nombre_mes(p.mes).capitalize()} {p.anio}  {peso_cl(p.monto)}" for p in pagos]
    return {
        "junta.nombre": junta.nombre,
        "nombre": vecino.nombre_completo,
        "nombre.socio": vecino.nombre_completo,
        "rut": rut_con_puntos(vecino.rut),
        "rut.socio": rut_con_puntos(vecino.rut),
        "domicilio": vecino.direccion or "",
        "fecha.pago": fecha.strftime("%d-%m-%Y"),
        "total": peso_cl(total),
        "presidente": junta.presidente or "la tesorería",
        "detalle.pagos": "\n".join(lineas) if lineas else "No hay pagos registrados en esta fecha.",
    }


__all__ = [
    "AYUDA_COMPROBANTE",
    "CUERPO_COMPROBANTE_DEFAULT",
    "PIE_COMPROBANTE_DEFAULT",
    "contexto_comprobante",
    "renderizar",
    "rut_con_puntos",
]
