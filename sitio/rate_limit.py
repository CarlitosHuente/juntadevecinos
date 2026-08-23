from django.core.cache import cache


def exceso_intentos(ip: str, accion: str, limite: int = 8, ventana: int = 600) -> bool:
    clave = f"rate:{accion}:{ip or 'anon'}"
    actuales = cache.get(clave, 0)
    if actuales >= limite:
        return True
    cache.set(clave, actuales + 1, ventana)
    return False


def ip_cliente(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
