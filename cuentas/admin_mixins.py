from cuentas.roles import Rol, apps_de_rol


class JuntaScopedAdminMixin:
    junta_field = "junta"

    def _es_plataforma(self, request) -> bool:
        user = request.user
        return user.is_superuser or getattr(user, "rol", None) == Rol.SUPERADMIN

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self._es_plataforma(request):
            return qs
        if getattr(request.user, "junta_id", None):
            return qs.filter(**{f"{self.junta_field}_id": request.user.junta_id})
        return qs.none()

    def save_model(self, request, obj, form, change):
        if hasattr(obj, "junta_id") and not obj.junta_id and getattr(request.user, "junta_id", None):
            obj.junta = request.user.junta
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "junta" and not self._es_plataforma(request) and request.user.junta_id:
            from juntas.models import Junta

            kwargs["queryset"] = Junta.objects.filter(pk=request.user.junta_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        if self._es_plataforma(request):
            return True
        app = getattr(self.model._meta, "app_label", "")
        return app in apps_de_rol(getattr(request.user, "rol", ""))

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
