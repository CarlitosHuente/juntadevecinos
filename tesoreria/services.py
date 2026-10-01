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


MESES_CORTO = ("", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")


def cuadro_anual(vecino, anio: int, hoy: date | None = None) -> dict:
    hoy = hoy or timezone.localdate()
    valor = Decimal(vecino.junta.valor_cuota or 0)
    ingreso = vecino.fecha_ingreso
    pagos = {p.mes: p.monto for p in vecino.pagos_cuota.all() if p.anio == anio}
    celdas = []
    for mes in range(1, 13):
        inicio_mes = date(anio, mes, 1)
        if ingreso and inicio_mes < date(ingreso.year, ingreso.month, 1):
            estado = "fuera"
        elif (anio, mes) > (hoy.year, hoy.month):
            estado = "futuro"
        elif valor <= 0:
            estado = "sin_cuota"
        elif mes in pagos:
            estado = "pagado"
        else:
            estado = "debe"
        celdas.append({"mes": mes, "corto": MESES_CORTO[mes], "estado": estado, "monto": pagos.get(mes)})

    debe_meses = [c["mes"] for c in celdas if c["estado"] == "debe"]
    pagados = [c["mes"] for c in celdas if c["estado"] == "pagado"]
    ultimo_pagado = max(pagados) if pagados else None
    if ultimo_pagado:
        hasta_texto = f"Pagó hasta {nombre_mes(ultimo_pagado)}"
    elif debe_meses:
        hasta_texto = "Sin pagos este año"
    else:
        hasta_texto = "Al día"
    if debe_meses:
        deuda_rango = f"{nombre_mes(debe_meses[0])} a {nombre_mes(debe_meses[-1])}"
        lectura = f"{hasta_texto} · debe {deuda_rango}"
    else:
        deuda_rango = ""
        lectura = hasta_texto
    return {
        "celdas": celdas,
        "es_moroso": bool(debe_meses),
        "ultimo_pagado": ultimo_pagado,
        "hasta_texto": hasta_texto,
        "deuda_rango": deuda_rango,
        "lectura": lectura,
        "monto_deuda": valor * len(debe_meses),
        "meses_deuda": len(debe_meses),
        "valor": valor,
    }


def socio_con_deuda(vecino) -> bool:
    if not vecino or not vecino.junta_id:
        return False
    return estado_cuotas(vecino)["tiene_deuda"]


def ultimo_dia(anio: int, mes: int) -> date:
    return date(anio, mes, monthrange(anio, mes)[1])
