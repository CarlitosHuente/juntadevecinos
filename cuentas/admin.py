from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from cuentas.admin_mixins import JuntaScopedAdminMixin
from cuentas.forms import UsuarioAltaForm, UsuarioCambioForm
from cuentas.models import Usuario
from cuentas.roles import (
    APPS_PANEL,
    GRUPOS_PROTEGIDOS,
    NOMBRE_GRUPO,
    Rol,
    aplicar_integrantes,
    asegurar_grupos,
    es_plataforma,
    rol_desde_grupos,
)

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class PermisosGrupoField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        verbo = obj.codename.split("_", 1)[0]
        accion = {"add": "Agregar", "change": "Cambiar", "delete": "Eliminar", "view": "Ver"}.get(verbo, verbo)
        modulo = {
            "juntas": "Junta",
            "cuentas": "Usuarios",
            "vecinos": "Socios",
            "contenido": "Contenido",
            "transparencia": "Transparencia",
            "tesoreria": "Tesorería",
            "auth": "Grupos",
        }.get(obj.content_type.app_label, obj.content_type.app_label)
        return f"{modulo} · {obj.content_type.name} · {accion}"


class GrupoForm(forms.ModelForm):
    permissions = PermisosGrupoField(
        label="Acciones",
        queryset=Permission.objects.none(),
        required=False,
        widget=FilteredSelectMultiple("acciones", is_stacked=False),
    )
    usuarios = forms.ModelMultipleChoiceField(
        label="Personas",
        queryset=Usuario.objects.none(),
        required=False,
        widget=FilteredSelectMultiple("personas", is_stacked=False),
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")

    def __init__(self, *args, alcance=None, **kwargs):
        super().__init__(*args, **kwargs)
        alcance = alcance if alcance is not None else Usuario.objects.all()
        self.fields["usuarios"].queryset = alcance.order_by("username")
        if self.instance.pk:
            self.fields["usuarios"].initial = alcance.filter(groups=self.instance)
        self.fields["name"].label = "Nombre del grupo"
        self.fields["permissions"].queryset = (
            Permission.objects.filter(content_type__app_label__in=APPS_PANEL)
            .exclude(content_type__app_label="auth", content_type__model="permission")
            .select_related("content_type")
        )
        self.fields["permissions"].help_text = (
            "Elige qué puede hacer este grupo: ver, agregar, cambiar o eliminar. "
            "Mañana puedes crear otro grupo (por ejemplo Tesorería) y marcar solo esas acciones, sin tocar el código."
        )


@admin.register(Group)
class GrupoAdmin(DjangoGroupAdmin, ModelAdmin):
    form = GrupoForm
    list_display = ("name", "cuantas_acciones", "cuantas_personas")
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def changelist_view(self, request, extra_context=None):
        asegurar_grupos()
        extra_context = extra_context or {}
        extra_context["title"] = "Grupos"
        extra_context["subtitle"] = (
            "Crea un grupo, marca sus acciones y asígnalo a las personas. Los grupos Directiva y Superadmin no se pueden borrar."
        )
        return super().changelist_view(request, extra_context=extra_context)

    def _alcance(self, request):
        qs = Usuario.objects.all()
        if es_plataforma(request.user):
            return qs
        if request.user.junta_id:
            return qs.filter(junta=request.user.junta).exclude(groups__name=NOMBRE_GRUPO[Rol.SUPERADMIN])
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        alcance = self._alcance(request)

        class Formulario(GrupoForm):
            def __init__(self, *args, **kw):
                kw.setdefault("alcance", alcance)
                super().__init__(*args, **kw)

        kwargs["form"] = Formulario
        kwargs["fields"] = ("name", "permissions")
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        return (
            (
                None,
                {
                    "fields": ("name",),
                    "description": "Crea o edita el grupo. Las acciones (ver, agregar, cambiar, eliminar) se marcan abajo.",
                },
            ),
            ("Acciones", {"fields": ("permissions",)}),
            ("Personas", {"fields": ("usuarios",)}),
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        aplicar_integrantes(obj, form.cleaned_data.get("usuarios") or [], self._alcance(request))

    def cuantas_acciones(self, obj):
        apps = list(obj.permissions.values_list("content_type__app_label", flat=True).distinct())
        etiquetas = {
            "juntas": "Junta",
            "cuentas": "Usuarios",
            "vecinos": "Socios",
            "contenido": "Contenido",
            "transparencia": "Transparencia",
            "tesoreria": "Tesorería",
            "auth": "Grupos",
        }
        nombres = [etiquetas.get(app, app) for app in apps]
        if not nombres:
            return "Sin acciones"
        return f"{obj.permissions.count()} · {', '.join(nombres)}"

    cuantas_acciones.short_description = "Acciones"

    def cuantas_personas(self, obj):
        return obj.user_set.count()

    cuantas_personas.short_description = "Personas"

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return es_plataforma(request.user) or request.user.has_module_perms("auth") or getattr(
            request.user, "rol", None
        ) == Rol.DIRECTIVA

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.name in GRUPOS_PROTEGIDOS:
            return False
        return self.has_module_permission(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not es_plataforma(request.user):
            qs = qs.exclude(name=NOMBRE_GRUPO[Rol.SUPERADMIN])
        return qs


@admin.register(Usuario)
class UsuarioAdmin(JuntaScopedAdminMixin, DjangoUserAdmin, ModelAdmin):
    form = UsuarioCambioForm
    add_form = UsuarioAltaForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "first_name", "last_name", "grupos_lista", "junta", "is_active")
    list_filter = ("groups", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    filter_horizontal = ("groups",)
    change_list_template = "admin/cuentas/usuario/change_list.html"

    def grupos_lista(self, obj):
        nombres = ", ".join(obj.groups.order_by("name").values_list("name", flat=True))
        return nombres or "—"

    grupos_lista.short_description = "Grupos"

    def get_fieldsets(self, request, obj=None):
        ayuda = format_html(
            'El acceso lo dan los <a href="{}">grupos</a>: crea uno nuevo o asigna Directiva, Comunicador, Secretario u otro.',
            reverse("admin:auth_group_changelist"),
        )
        if not obj:
            campos = ("username", "password1", "password2", "first_name", "last_name", "email", "groups")
            if self._es_plataforma(request):
                campos += ("junta",)
            return (("Nuevo usuario", {"classes": ("wide",), "fields": campos, "description": ayuda}),)
        if self._es_plataforma(request):
            return (
                ("Grupos", {"fields": ("groups", "junta"), "description": ayuda}),
                (None, {"fields": ("username", "password")}),
                ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
                ("Estado", {"fields": ("is_active", "is_staff", "is_superuser")}),
            )
        return (
            ("Grupos", {"fields": ("groups",), "description": ayuda}),
            (None, {"fields": ("username", "password")}),
            ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
            ("Estado", {"fields": ("is_active",)}),
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" and not self._es_plataforma(request):
            kwargs["queryset"] = Group.objects.exclude(name=NOMBRE_GRUPO[Rol.SUPERADMIN])
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not self._es_plataforma(request):
            obj.junta = request.user.junta
            obj.is_superuser = False
            obj.is_staff = True
        else:
            obj.is_staff = True
            if not obj.junta_id and request.user.junta_id:
                obj.junta = request.user.junta
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        usuario = form.instance
        Usuario.objects.filter(pk=usuario.pk).update(rol=rol_desde_grupos(usuario))

    def get_queryset(self, request):
        qs = super(DjangoUserAdmin, self).get_queryset(request)
        if self._es_plataforma(request):
            return qs
        if request.user.junta_id:
            return qs.filter(junta=request.user.junta).exclude(groups__name=NOMBRE_GRUPO[Rol.SUPERADMIN])
        return qs.none()
