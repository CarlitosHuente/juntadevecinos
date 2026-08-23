from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from cuentas.admin_mixins import JuntaScopedAdminMixin
from cuentas.models import Usuario
from cuentas.roles import Rol


@admin.register(Usuario)
class UsuarioAdmin(JuntaScopedAdminMixin, DjangoUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "last_name", "rol", "junta", "is_staff")
    list_filter = ("rol", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Junta y rol", {"fields": ("junta", "rol")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Junta y rol", {"fields": ("junta", "rol")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.rol != Rol.SUPERADMIN and not obj.junta_id and request.user.junta_id:
            obj.junta = request.user.junta
        if obj.rol != Rol.SUPERADMIN:
            obj.is_staff = True
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super(DjangoUserAdmin, self).get_queryset(request)
        if request.user.is_superuser or getattr(request.user, "rol", None) == Rol.SUPERADMIN:
            return qs
        if request.user.junta_id:
            return qs.filter(junta=request.user.junta).exclude(rol=Rol.SUPERADMIN)
        return qs.none()
