import re

_RUT_LIMPIO = re.compile(r"[^0-9kK]")


def normalizar_rut(valor: str) -> str:
    limpio = _RUT_LIMPIO.sub("", (valor or "").strip()).upper()
    if len(limpio) < 2:
        return limpio
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{cuerpo}-{dv}"


def validar_rut(valor: str) -> bool:
    rut = normalizar_rut(valor)
    if not re.fullmatch(r"\d{7,8}-[\dK]", rut):
        return False
    cuerpo, dv = rut.split("-")
    return _digito_verificador(cuerpo) == dv


def _digito_verificador(cuerpo: str) -> str:
    factores = [2, 3, 4, 5, 6, 7]
    total = 0
    for i, digito in enumerate(reversed(cuerpo)):
        total += int(digito) * factores[i % 6]
    resto = 11 - (total % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)
