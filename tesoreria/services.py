from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.utils import timezone


def periodos_desde(inicio: date, hasta: date | None = None) -> list[tuple[int, int]]:
    if not inicio:
        return []
    hasta = hasta or timezone.localdate()
    if inicio > hasta:
        return []
    periodos = []
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (hasta.year, hasta.month):
        periodos.append((anio, mes))
        if mes == 12:
            anio, mes = anio + 1, 1
        else:
            mes += 1
    return periodos


def nombre_mes(mes: int) -> str:
    nombres = (
        "",
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )
    return nombres[mes] if 1 <= mes <= 12 else str(mes)


def estado_cuotas(vecino) -> dict:
    junta = vecino.junta
    valor = Decimal(junta.valor_cuota or 0)
    periodos = periodos_desde(vecino.fecha_ingreso) if valor > 0 else []
    pagados = set(vecino.pagos_cuota.values_list("anio", "mes"))
    adeudados = [p for p in periodos if p not in pagados]
    return {
        "valor": valor,
        "periodos": periodos,
        "pagados": sorted(pagados),
        "adeudados": adeudados,
        "meses_pagados": len(periodos) - len(adeudados),
        "meses_deuda": len(adeudados),
        "monto_pagado": valor * (len(periodos) - len(adeudados)),
        "monto_deuda": valor * len(adeudados),
        "tiene_deuda": bool(adeudados),
    }


def socio_con_deuda(vecino) -> bool:
    if not vecino or not vecino.junta_id:
        return False
    return estado_cuotas(vecino)["tiene_deuda"]


def ultimo_dia(anio: int, mes: int) -> date:
    return date(anio, mes, monthrange(anio, mes)[1])
