from django.contrib import admin
from unfold.admin import ModelAdmin

from contenido.widgets import RecorteImagenMixin
from cuentas.admin_mixins import JuntaScopedAdminMixin
from transparencia.models import InformeActividad, RendicionGasto


@admin.register(RendicionGasto)
class RendicionGastoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("fecha", "concepto", "categoria", "monto", "publicada", "junta")
    list_filter = ("categoria", "publicada", "junta")
    search_fields = ("concepto", "descripcion")
    list_editable = ("publicada",)


@admin.register(InformeActividad)
class InformeActividadAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    recorte_campos = {
        "imagen": {"ratio": "16/10", "etiqueta": "Así se verá en Transparencia"},
    }
    list_display = ("fecha", "titulo", "publicada", "junta")
    list_filter = ("publicada", "junta")
    search_fields = ("titulo", "descripcion")
    list_editable = ("publicada",)
