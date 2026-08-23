from django.contrib import admin
from unfold.admin import ModelAdmin

from cuentas.admin_mixins import JuntaScopedAdminMixin
from cuentas.roles import Rol
from juntas.models import Junta


@admin.register(Junta)
class JuntaAdmin(JuntaScopedAdminMixin, ModelAdmin):
    junta_field = "id"
    list_display = ("nombre", "slug", "comuna", "presidente", "activa")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre", "slug", "comuna")
    list_filter = ("activa",)

    def get_queryset(self, request):
        qs = super(ModelAdmin, self).get_queryset(request)
        user = request.user
        if user.is_superuser or getattr(user, "rol", None) == Rol.SUPERADMIN:
            return qs
        if getattr(user, "junta_id", None):
            return qs.filter(pk=user.junta_id)
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, "rol", None) == Rol.SUPERADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, "rol", None) == Rol.SUPERADMIN
