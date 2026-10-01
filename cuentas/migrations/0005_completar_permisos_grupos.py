from django.apps import apps as django_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations

from cuentas.roles import NOMBRE_GRUPO, Rol


def completar_permisos(apps, schema_editor):
    for app_config in django_apps.get_app_configs():
        create_permissions(app_config, verbosity=0)

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
        actuales = set(grupo.permissions.values_list("pk", flat=True))
        faltantes = list(
            Permission.objects.filter(content_type__app_label__in=apps_por_rol[clave]).exclude(pk__in=actuales)
        )
        if faltantes:
            grupo.permissions.add(*faltantes)


def vaciar(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("contenido", "0003_galeria_fotos_noticia_evento"),
        ("cuentas", "0004_permisos_django_grupos"),
        ("juntas", "0004_tesoreria_cuotas_y_directiva"),
        ("tesoreria", "0002_diseno_comprobante"),
        ("transparencia", "0001_initial"),
        ("vecinos", "0006_disenocertificado_layout"),
    ]

    operations = [
        migrations.RunPython(completar_permisos, vaciar),
    ]
