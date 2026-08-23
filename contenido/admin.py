from django.contrib import admin
from unfold.admin import ModelAdmin

from contenido.models import Evento, Noticia, SlideCarrusel
from cuentas.admin_mixins import JuntaScopedAdminMixin


@admin.register(Noticia)
class NoticiaAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("titulo", "publicada", "destacada", "publicada_en", "junta")
    list_filter = ("publicada", "destacada", "junta")
    search_fields = ("titulo", "bajada", "cuerpo")
    prepopulated_fields = {"slug": ("titulo",)}
    list_editable = ("publicada", "destacada")

    def save_model(self, request, obj, form, change):
        if not obj.autor_id:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


@admin.register(Evento)
class EventoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("titulo", "fecha_inicio", "lugar", "publicado", "junta")
    list_filter = ("publicado", "junta")
    search_fields = ("titulo", "descripcion", "lugar")
    prepopulated_fields = {"slug": ("titulo",)}


@admin.register(SlideCarrusel)
class SlideCarruselAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("titulo", "orden", "activo", "junta")
    list_editable = ("orden", "activo")
