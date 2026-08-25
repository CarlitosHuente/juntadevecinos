from django.db import migrations


def rellenar(apps, schema_editor):
    Certificado = apps.get_model("vecinos", "Certificado")
    DisenoCertificado = apps.get_model("vecinos", "DisenoCertificado")
    for cert in Certificado.objects.select_related("vecino").all():
        if cert.vecino_id and not cert.nombre_impreso:
            cert.nombre_impreso = f"{cert.vecino.nombres} {cert.vecino.apellido_paterno}".strip()
            cert.rut_impreso = cert.vecino.rut
            cert.direccion_impresa = cert.vecino.direccion
            cert.save(update_fields=["nombre_impreso", "rut_impreso", "direccion_impresa"])
        if cert.junta_id:
            DisenoCertificado.objects.get_or_create(junta_id=cert.junta_id)


def vaciar(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("vecinos", "0003_alter_certificado_options_and_more"),
    ]

    operations = [
        migrations.RunPython(rellenar, vaciar),
    ]
