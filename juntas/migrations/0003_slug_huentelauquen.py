from django.db import migrations


def renombrar_slug(apps, schema_editor):
    Junta = apps.get_model("juntas", "Junta")
    if Junta.objects.filter(slug="huentelauquen").exists():
        return
    Junta.objects.filter(slug="huente").update(slug="huentelauquen")


class Migration(migrations.Migration):
    dependencies = [
        ("juntas", "0002_alter_junta_presidente_cargodirectiva"),
    ]

    operations = [
        migrations.RunPython(renombrar_slug, migrations.RunPython.noop),
    ]
