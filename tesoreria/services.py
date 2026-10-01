from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

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
        "monto_pagado": sum((c["monto"] or Decimal(0) for c in celdas if c["estado"] == "pagado"), Decimal(0)),
        "meses_deuda": len(debe_meses),
        "valor": valor,
    }


def socio_con_deuda(vecino) -> bool:
    if not vecino or not vecino.junta_id:
        return False
    return estado_cuotas(vecino)["tiene_deuda"]


def ultimo_dia(anio: int, mes: int) -> date:
    return date(anio, mes, monthrange(anio, mes)[1])


def parsear_monto(texto) -> Decimal | None:
    crudo = str(texto or "").strip().replace("$", "").replace(" ", "")
    if not crudo:
        return None
    if "," in crudo and "." in crudo:
        if crudo.rfind(",") > crudo.rfind("."):
            crudo = crudo.replace(".", "").replace(",", ".")
        else:
            crudo = crudo.replace(",", "")
    elif "," in crudo:
        partes = crudo.split(",")
        crudo = crudo.replace(",", "") if len(partes[-1]) == 3 and len(partes) > 1 else crudo.replace(",", ".")
    elif "." in crudo:
        partes = crudo.split(".")
        if len(partes[-1]) == 3:
            crudo = crudo.replace(".", "")
    try:
        valor = Decimal(crudo)
    except InvalidOperation:
        return None
    if valor < 0:
        return None
    return valor.quantize(Decimal("1"))


def parsear_fecha(texto, defecto: date | None = None) -> date:
    defecto = defecto or timezone.localdate()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime((texto or "").strip(), fmt).date()
        except ValueError:
            continue
    return defecto


def peso_cl(monto) -> str:
    entero = int(Decimal(monto or 0))
    return f"${entero:,}".replace(",", ".")


def detalle_movimiento_cuota(pago) -> str:
    return f"Cuota {pago.mes:02d}/{pago.anio} · {pago.vecino.nombre_completo}"


def sincronizar_movimiento_cuota(pago) -> None:
    from tesoreria.models import Movimiento

    Movimiento.objects.update_or_create(
        junta=pago.vecino.junta,
        tipo=Movimiento.Tipo.INGRESO,
        categoria="cuota",
        socio=pago.vecino,
        detalle=detalle_movimiento_cuota(pago),
        defaults={"fecha": pago.pagado_en, "monto": pago.monto},
    )


def borrar_movimiento_cuota(pago) -> None:
    from tesoreria.models import Movimiento

    Movimiento.objects.filter(
        junta=pago.vecino.junta,
        tipo=Movimiento.Tipo.INGRESO,
        categoria="cuota",
        socio=pago.vecino,
        detalle=detalle_movimiento_cuota(pago),
    ).delete()


def mes_habilitado(vecino, anio: int, mes: int) -> bool:
    ingreso = vecino.fecha_ingreso
    if not ingreso:
        return True
    return date(anio, mes, 1) >= date(ingreso.year, ingreso.month, 1)


def aplicar_pagos_masivos(socios, anio: int, fecha: date, post) -> int:
    from tesoreria.models import PagoCuota

    cambios = 0
    for socio in socios:
        for mes in range(1, 13):
            clave = f"p_{socio.id}_{mes}"
            if clave not in post:
                continue
            if not mes_habilitado(socio, anio, mes):
                continue
            monto = parsear_monto(post.get(clave))
            existente = PagoCuota.objects.filter(vecino=socio, anio=anio, mes=mes).first()
            if monto is None or monto <= 0:
                if existente:
                    borrar_movimiento_cuota(existente)
                    existente.delete()
                    cambios += 1
                continue
            if existente:
                if existente.monto == monto:
                    continue
                existente.monto = monto
                existente.pagado_en = fecha
                existente.save()
                sincronizar_movimiento_cuota(existente)
            else:
                pago = PagoCuota.objects.create(
                    vecino=socio,
                    anio=anio,
                    mes=mes,
                    monto=monto,
                    pagado_en=fecha,
                )
                sincronizar_movimiento_cuota(pago)
            cambios += 1
    return cambios


def pagos_del_dia(vecino, fecha: date):
    return list(vecino.pagos_cuota.filter(pagado_en=fecha).order_by("anio", "mes"))


def nombre_comprobante(vecino, fecha: date) -> str:
    limpio = " ".join((vecino.nombre_completo or "socio").split())
    return f"{limpio} {fecha.strftime('%d-%m-%Y')}.pdf"
