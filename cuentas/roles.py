from django.contrib.auth.models import Group, Permission

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
        SUPERADMIN: {"juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria", "auth"},
        DIRECTIVA: {"juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria", "auth"},
        COMUNICADOR: {"contenido", "transparencia"},
        SECRETARIO: {"vecinos"},
    }


NOMBRE_GRUPO = {
    Rol.SUPERADMIN: "Superadmin",
    Rol.DIRECTIVA: "Directiva",
    Rol.COMUNICADOR: "Comunicador",
    Rol.SECRETARIO: "Secretario",
}

CLAVE_GRUPO = {nombre: clave for clave, nombre in NOMBRE_GRUPO.items()}
APPS_PANEL = ("juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria", "auth")
GRUPOS_PROTEGIDOS = {NOMBRE_GRUPO[Rol.SUPERADMIN], NOMBRE_GRUPO[Rol.DIRECTIVA]}


def es_plataforma(user) -> bool:
    if user.is_superuser or getattr(user, "rol", None) == Rol.SUPERADMIN:
        return True
    if not getattr(user, "pk", None):
        return False
    return user.groups.filter(name=NOMBRE_GRUPO[Rol.SUPERADMIN]).exists()


def apps_de_rol(rol: str) -> set[str]:
    return set(Rol.APPS_PERMITIDAS.get(rol, set()))


def roles_asignables(es_plataforma_ok: bool) -> tuple[tuple[str, str], ...]:
    if es_plataforma_ok:
        return Rol.CHOICES
    return tuple(c for c in Rol.CHOICES if c[0] != Rol.SUPERADMIN)


def permisos_de_apps(app_labels) -> list:
    return list(Permission.objects.filter(content_type__app_label__in=set(app_labels)))


def asegurar_grupos() -> dict:
    grupos = {}
    for clave, nombre in NOMBRE_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        actuales = set(grupo.permissions.values_list("pk", flat=True))
        faltantes = [p for p in permisos_de_apps(Rol.APPS_PERMITIDAS[clave]) if p.pk not in actuales]
        if faltantes:
            grupo.permissions.add(*faltantes)
        grupos[clave] = grupo
    return grupos


def agregar_grupo_inicial(usuario) -> None:
    if not usuario.pk or usuario.groups.exists():
        return
    asegurar_grupos()
    nombre = NOMBRE_GRUPO.get(usuario.rol)
    if not nombre:
        return
    grupo = Group.objects.filter(name=nombre).first()
    if grupo:
        usuario.groups.add(grupo)


def rol_desde_grupos(usuario) -> str:
    nombres = set(usuario.groups.values_list("name", flat=True))
    for clave, nombre in NOMBRE_GRUPO.items():
        if nombre in nombres:
            return clave
    return usuario.rol or Rol.COMUNICADOR


def aplicar_integrantes(grupo, integrantes, alcance) -> None:
    elegidos = {u.pk for u in integrantes}
    actuales = set(alcance.filter(groups=grupo).values_list("pk", flat=True))
    for usuario in alcance.filter(pk__in=elegidos - actuales):
        usuario.groups.add(grupo)
        usuario.is_staff = True
        Usuario = type(usuario)
        Usuario.objects.filter(pk=usuario.pk).update(is_staff=True, rol=rol_desde_grupos(usuario))
    for usuario in alcance.filter(pk__in=actuales - elegidos):
        usuario.groups.remove(grupo)
        Usuario = type(usuario)
        Usuario.objects.filter(pk=usuario.pk).update(rol=rol_desde_grupos(usuario))
