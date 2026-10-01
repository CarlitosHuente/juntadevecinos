from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from contenido.models import Evento, FotoEvento, FotoNoticia, Noticia, SlideCarrusel
from contenido.widgets import RecorteImagenMixin
from cuentas.admin_mixins import JuntaScopedAdminMixin


class FotoNoticiaInline(RecorteImagenMixin, TabularInline):
    model = FotoNoticia
    extra = 3
    fields = ("imagen", "pie", "orden")
    verbose_name_plural = "Galería: sube varias fotos de la actividad"
    recorte_campos = {
        "imagen": {"ratio": "4/3", "etiqueta": "Así se verá en la galería"},
    }


class FotoEventoInline(RecorteImagenMixin, TabularInline):
    model = FotoEvento
    extra = 3
    fields = ("imagen", "pie", "orden")
    verbose_name_plural = "Galería: fotos del día"
    recorte_campos = {
        "imagen": {"ratio": "4/3", "etiqueta": "Así se verá en la galería"},
    }


class ArticuloAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            "cuerpo": forms.Textarea(attrs={"rows": 16}),
            "descripcion": forms.Textarea(attrs={"rows": 16}),
            "bajada": forms.TextInput(attrs={"placeholder": "Una frase que invite a leer"}),
        }


@admin.register(Noticia)
class NoticiaAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    recorte_campos = {
        "imagen": {"ratio": "16/10", "etiqueta": "Así se verá la portada en noticias y en el inicio"},
    }
    form = ArticuloAdminForm
    list_display = ("titulo", "publicada", "destacada", "publicada_en", "junta")
    list_filter = ("publicada", "destacada", "junta")
    search_fields = ("titulo", "bajada", "cuerpo")
    prepopulated_fields = {"slug": ("titulo",)}
    list_editable = ("publicada", "destacada")
    inlines = [FotoNoticiaInline]
    fieldsets = (
        (
            "El artículo",
            {
                "fields": ("junta", "titulo", "bajada", "cuerpo"),
                "description": "Escríbelo como un blog: título, una frase de entrada y el relato.",
            },
        ),
        (
            "Foto de portada",
            {
                "fields": ("imagen",),
                "description": "Sube la foto y encuádrala. Lo que ves en el recuadro es lo que sale en el inicio y en la noticia.",
            },
        ),
        (
            "Publicación",
            {"fields": ("slug", "publicada_en", "publicada", "destacada")},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.autor_id:
            obj.autor = request.user
        super().save_model(request, obj, form, change)


@admin.register(Evento)
class EventoAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    recorte_campos = {
        "imagen": {"ratio": "16/10", "etiqueta": "Así se verá la portada del evento"},
    }
    form = ArticuloAdminForm
    list_display = ("titulo", "fecha_inicio", "lugar", "publicado", "junta")
    list_filter = ("publicado", "junta")
    search_fields = ("titulo", "descripcion", "lugar")
    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [FotoEventoInline]
    fieldsets = (
        (
            "La actividad",
            {
                "fields": ("junta", "titulo", "lugar", "fecha_inicio", "fecha_fin", "descripcion"),
                "description": "Cuenta qué se hizo y dónde. Las fotos son lo que más se comparte.",
            },
        ),
        (
            "Foto de portada",
            {
                "fields": ("imagen",),
                "description": "Sube la foto y muévela o recórtala hasta que quede como en el inicio.",
            },
        ),
        (
            "Publicación",
            {"fields": ("slug", "publicado")},
        ),
    )


@admin.register(SlideCarrusel)
class SlideCarruselAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("titulo", "orden", "activo", "junta")
    list_editable = ("orden", "activo")
    recorte_campos = {
        "imagen": {"ratio": "16/7", "etiqueta": "Así se verá el slide en el inicio"},
    }
    fieldsets = (
        (
            "Mensaje",
            {"fields": ("junta", "titulo", "texto", "enlace", "orden", "activo")},
        ),
        (
            "Imagen",
            {
                "fields": ("imagen",),
                "description": "Carga la foto, acércala y arrástrala. El recuadro es el mismo formato del carrusel.",
            },
        ),
        (
            "Vigencia (opcional)",
            {"fields": ("desde", "hasta")},
        ),
    )
