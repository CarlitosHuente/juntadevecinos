from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cuentas"
    verbose_name = "Usuarios y grupos"

    def ready(self):
        from django.contrib.auth.models import Group

        Group._meta.verbose_name = "Grupo"
        Group._meta.verbose_name_plural = "Grupos"
