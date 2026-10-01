from django.db import migrations, models

from cuentas.roles import NOMBRE_GRUPO


def crear_grupos_y_sincronizar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Usuario = apps.get_model("cuentas", "Usuario")
    grupos = {clave: Group.objects.get_or_create(name=nombre)[0] for clave, nombre in NOMBRE_GRUPO.items()}
    through = Usuario.groups.through
    for usuario in Usuario.objects.all():
        grupo = grupos.get(usuario.rol)
        if not grupo:
            continue
        through.objects.filter(usuario_id=usuario.id).delete()
        through.objects.get_or_create(usuario_id=usuario.id, group_id=grupo.id)


def vaciar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=NOMBRE_GRUPO.values()).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("cuentas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GrupoRol",
            fields=[],
            options={
                "verbose_name": "Grupo / rol",
                "verbose_name_plural": "Grupos / roles",
                "proxy": True,
            },
            bases=("auth.group",),
        ),
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("superadmin", "Superadmin"),
                    ("directiva", "Directiva"),
                    ("comunicador", "Comunicador"),
                    ("secretario", "Secretario"),
                ],
                default="comunicador",
                max_length=20,
                verbose_name="Grupo / rol",
            ),
        ),
        migrations.RunPython(crear_grupos_y_sincronizar, vaciar),
    ]
