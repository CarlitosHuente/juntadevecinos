from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from contenido.widgets import RecorteImagenMixin
from cuentas.admin_mixins import JuntaScopedAdminMixin
from cuentas.roles import Rol
from juntas.models import CargoDirectiva, Junta
from juntas.widgets import ColorPaletaWidget


class CargoDirectivaInline(RecorteImagenMixin, TabularInline):
    recorte_campos = {
        "foto": {"ratio": "3/4", "etiqueta": "Así se verá la foto en Quiénes somos"},
    }
    model = CargoDirectiva
    extra = 1
    fields = ("orden", "cargo", "nombre", "rut", "email", "telefono", "periodo", "foto")


@admin.register(Junta)
class JuntaAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    recorte_campos = {
        "logo": {"ratio": "1/1", "etiqueta": "Así se verá el logo en el encabezado"},
    }
    junta_field = "id"
    list_display = ("nombre", "slug", "comuna", "presidente", "activa")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre", "slug", "comuna")
    list_filter = ("activa",)
    inlines = [CargoDirectivaInline]
    fieldsets = (
        (
            "Identidad del sitio",
            {
                "fields": ("nombre", "slug", "logo", "activa"),
                "description": "El logo aparece en el encabezado de la web y en celulares.",
            },
        ),
        (
            "Colores",
            {
                "fields": ("color_primario", "color_acento", "color_apoyo"),
                "description": "Pulsa el recuadro para abrir la paleta, o elige un color sugerido. El código queda guardado por si lo necesitas.",
            },
        ),
        (
            "Sede y contacto",
            {"fields": ("direccion", "comuna", "telefono", "email")},
        ),
        (
            "Quiénes somos",
            {
                "fields": ("descripcion", "presidente"),
                "description": "La ficha de cada integrante se edita en Directiva.",
            },
        ),
        (
            "Tesorería y certificados",
            {
                "fields": ("valor_cuota", "certificado_con_deuda"),
                "description": "Define la cuota mensual y si un socio con deuda puede pedir certificado en la web.",
            },
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        if campo and db_field.name in {"color_primario", "color_acento", "color_apoyo"}:
            campo.widget = ColorPaletaWidget()
            campo.help_text = "Pulsa el recuadro grande para ver la paleta."
        return campo

    def get_queryset(self, request):
        qs = super(ModelAdmin, self).get_queryset(request)
        user = request.user
        if user.is_superuser or getattr(user, "rol", None) == Rol.SUPERADMIN:
            return qs
        if getattr(user, "junta_id", None):
            return qs.filter(pk=user.junta_id)
        return qs.none()

    def get_readonly_fields(self, request, obj=None):
        if self._es_plataforma(request):
            return self.readonly_fields
        return tuple(self.readonly_fields) + ("slug", "activa")

    def get_prepopulated_fields(self, request, obj=None):
        if self._es_plataforma(request):
            return self.prepopulated_fields
        return {}

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, "rol", None) == Rol.SUPERADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, "rol", None) == Rol.SUPERADMIN


@admin.register(CargoDirectiva)
class CargoDirectivaAdmin(RecorteImagenMixin, JuntaScopedAdminMixin, ModelAdmin):
    recorte_campos = {
        "foto": {"ratio": "3/4", "etiqueta": "Así se verá la foto en Quiénes somos"},
    }
    list_display = ("nombre", "cargo", "periodo", "telefono", "email", "junta")
    list_filter = ("cargo", "junta")
    search_fields = ("nombre", "cargo", "rut", "email")
    fieldsets = (
        (
            "Integrante",
            {
                "fields": ("junta", "cargo", "nombre", "foto", "orden"),
                "description": "Cada persona de la directiva tiene su propia ficha.",
            },
        ),
        (
            "Datos de contacto",
            {"fields": ("rut", "email", "telefono", "periodo", "descripcion")},
        ),
    )

    def get_list_filter(self, request):
        if self._es_plataforma(request):
            return self.list_filter
        return ("cargo",)

    def get_list_display(self, request):
        if self._es_plataforma(request):
            return self.list_display
        return tuple(c for c in self.list_display if c != "junta")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if self._es_plataforma(request):
            return fieldsets
        limpios = []
        for titulo, opts in fieldsets:
            campos = tuple(c for c in opts.get("fields", ()) if c != "junta")
            limpios.append((titulo, {**opts, "fields": campos}))
        return limpios
