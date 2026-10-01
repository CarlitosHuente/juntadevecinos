from django.db import migrations

from cuentas.roles import NOMBRE_GRUPO, Rol


def asignar_permisos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    apps_por_rol = {
        Rol.SUPERADMIN: {"juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria", "auth"},
        Rol.DIRECTIVA: {"juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria", "auth"},
        Rol.COMUNICADOR: {"contenido", "transparencia"},
        Rol.SECRETARIO: {"vecinos"},
    }
    for clave, nombre in NOMBRE_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        if grupo.permissions.exists():
            continue
        permisos = Permission.objects.filter(content_type__app_label__in=apps_por_rol[clave])
        grupo.permissions.set(permisos)


def vaciar(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("cuentas", "0003_permisogrupo"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos, vaciar),
    ]
