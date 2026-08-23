from django.contrib import admin
from unfold.admin import ModelAdmin

from cuentas.admin_mixins import JuntaScopedAdminMixin
from vecinos.models import Certificado, Vecino


@admin.register(Vecino)
class VecinoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = (
        "rut",
        "nombres",
        "apellido_paterno",
        "direccion",
        "activo",
        "mostrar_cumpleanos",
        "junta",
    )
    list_filter = ("activo", "mostrar_cumpleanos", "junta")
    search_fields = ("rut", "nombres", "apellido_paterno", "apellido_materno", "direccion")
    list_editable = ("activo", "mostrar_cumpleanos")


@admin.register(Certificado)
class CertificadoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("codigo", "vecino", "emitido_en", "anulado", "junta")
    list_filter = ("anulado", "junta")
    search_fields = ("codigo", "vecino__rut", "vecino__nombres", "vecino__apellido_paterno")
    readonly_fields = ("codigo", "contenido_hash", "emitido_en", "ip_solicitud", "vecino", "junta")

    def has_add_permission(self, request):
        return False
