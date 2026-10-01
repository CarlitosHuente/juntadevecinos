from django.db import migrations, models
import django.db.models.deletion

from cuentas.roles import NOMBRE_GRUPO, Rol


def sembrar_permisos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    PermisoGrupo = apps.get_model("cuentas", "PermisoGrupo")
    defaults = {
        Rol.SUPERADMIN: dict(juntas=True, cuentas=True, vecinos=True, contenido=True, transparencia=True, tesoreria=True),
        Rol.DIRECTIVA: dict(juntas=True, cuentas=True, vecinos=True, contenido=True, transparencia=True, tesoreria=True),
        Rol.COMUNICADOR: dict(juntas=False, cuentas=False, vecinos=False, contenido=True, transparencia=True, tesoreria=False),
        Rol.SECRETARIO: dict(juntas=False, cuentas=False, vecinos=True, contenido=False, transparencia=False, tesoreria=False),
    }
    for clave, nombre in NOMBRE_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        PermisoGrupo.objects.get_or_create(grupo=grupo, defaults=defaults[clave])


def vaciar(apps, schema_editor):
    PermisoGrupo = apps.get_model("cuentas", "PermisoGrupo")
    PermisoGrupo.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("cuentas", "0002_grupos_predeterminados"),
    ]

    operations = [
        migrations.CreateModel(
            name="PermisoGrupo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("juntas", models.BooleanField(default=False, verbose_name="Junta (sede, logo, colores)")),
                ("cuentas", models.BooleanField(default=False, verbose_name="Usuarios y grupos")),
                ("vecinos", models.BooleanField(default=False, verbose_name="Socios y certificados")),
                ("contenido", models.BooleanField(default=False, verbose_name="Noticias, eventos y slides")),
                ("transparencia", models.BooleanField(default=False, verbose_name="Transparencia")),
                ("tesoreria", models.BooleanField(default=False, verbose_name="Tesorería y cuotas")),
                (
                    "grupo",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permisos_panel",
                        to="auth.group",
                        verbose_name="Grupo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Permisos del grupo",
                "verbose_name_plural": "Permisos de grupos",
            },
        ),
        migrations.RunPython(sembrar_permisos, vaciar),
    ]
