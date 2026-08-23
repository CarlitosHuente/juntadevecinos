class Rol:
    SUPERADMIN = "superadmin"
    DIRECTIVA = "directiva"
    COMUNICADOR = "comunicador"
    SECRETARIO = "secretario"

    CHOICES = (
        (SUPERADMIN, "Superadmin"),
        (DIRECTIVA, "Directiva"),
        (COMUNICADOR, "Comunicador"),
        (SECRETARIO, "Secretario"),
    )

    APPS_PERMITIDAS = {
        SUPERADMIN: {"juntas", "cuentas", "vecinos", "contenido"},
        DIRECTIVA: {"juntas", "cuentas", "vecinos", "contenido"},
        COMUNICADOR: {"contenido"},
        SECRETARIO: {"vecinos"},
    }


def apps_de_rol(rol: str) -> set[str]:
    return Rol.APPS_PERMITIDAS.get(rol, set())
