import json
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from cuentas.admin_mixins import JuntaScopedAdminMixin
from cuentas.roles import Rol
from vecinos.importar import importar_familiares, importar_socios, plantilla_familiares, plantilla_socios
from vecinos.layout import BLOQUES, layout_completo, layout_por_defecto
from vecinos.models import AYUDA_VARIABLES, Certificado, DisenoCertificado, Familiar, Vecino
from vecinos.pdf import construir_pdf
from vecinos.services import completar_desde_relaciones, crear_certificado, pdf_de_certificado
from vecinos.variables import certificado_muestra, contexto_certificado, renderizar


class CertificadoAdminForm(forms.ModelForm):
    class Meta:
        model = Certificado
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("nombre_impreso", "rut_impreso", "direccion_impresa", "codigo", "contenido_hash"):
            if campo in self.fields:
                self.fields[campo].required = False

    def clean(self):
        cleaned = super().clean()
        temporal = Certificado(
            vecino=cleaned.get("vecino"),
            familiar=cleaned.get("familiar"),
            nombre_impreso=cleaned.get("nombre_impreso") or "",
            rut_impreso=cleaned.get("rut_impreso") or "",
            direccion_impresa=cleaned.get("direccion_impresa") or "",
        )
        completar_desde_relaciones(temporal)
        if not temporal.nombre_impreso:
            raise ValidationError("Indica un nombre o elige un socio / familiar.")
        if not temporal.direccion_impresa:
            raise ValidationError("Indica el domicilio o elige un socio titular.")
        cleaned["nombre_impreso"] = temporal.nombre_impreso
        cleaned["rut_impreso"] = temporal.rut_impreso
        cleaned["direccion_impresa"] = temporal.direccion_impresa
        cleaned["vecino"] = temporal.vecino
        return cleaned


class FamiliarInline(TabularInline):
    model = Familiar
    extra = 2
    fields = ("nombre", "rut", "fecha_nacimiento", "email", "telefono")
    verbose_name = "Integrante"
    verbose_name_plural = "Grupo familiar (solo el nombre es obligatorio)"


class ImportacionExcelMixin:
    def _junta_importacion(self, request):
        return request.user.junta

    def _respuesta_plantilla(self, contenido, nombre):
        response = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return response

    def _importar_vista(self, request, tipo):
        junta = self._junta_importacion(request)
        if not junta:
            messages.error(request, "Tu usuario no tiene una junta asignada.")
            destino = (
                "admin:vecinos_vecino_changelist"
                if tipo == "socios"
                else "admin:vecinos_familiar_changelist"
            )
            return redirect(destino)
        resultado = None
        if request.method == "POST" and request.FILES.get("archivo"):
            archivo = request.FILES["archivo"]
            if tipo == "socios":
                resultado = importar_socios(junta, archivo)
            else:
                resultado = importar_familiares(junta, archivo)
            if resultado["creados"]:
                messages.success(request, f"Se cargaron {resultado['creados']} registros.")
            if resultado["errores"]:
                messages.warning(request, "Revisa las filas que no se pudieron cargar.")
        volver = (
            "admin:vecinos_vecino_changelist"
            if tipo == "socios"
            else "admin:vecinos_familiar_changelist"
        )
        if tipo == "socios":
            columnas = [
                {"nombre": "RUT", "obligatoria": True, "ejemplo": "12.345.678-5"},
                {"nombre": "Nombres", "obligatoria": True, "ejemplo": "Juan"},
                {"nombre": "Apellido paterno", "obligatoria": True, "ejemplo": "Pérez"},
                {"nombre": "Apellido materno", "obligatoria": False, "ejemplo": "Soto"},
                {"nombre": "Dirección", "obligatoria": True, "ejemplo": "Pasaje 1"},
                {"nombre": "Fecha nacimiento", "obligatoria": False, "ejemplo": "12-05-1980"},
                {"nombre": "Correo", "obligatoria": False, "ejemplo": "juan@correo.cl"},
                {"nombre": "Teléfono", "obligatoria": False, "ejemplo": "+56 9 1111 1111"},
                {"nombre": "Fecha ingreso", "obligatoria": False, "ejemplo": "01-03-2024"},
            ]
            intro = "Carga varios socios titulares de una vez. Primero descarga la plantilla, completa una fila por persona y súbela."
            ayuda = "Fechas en DD-MM-AAAA (ejemplo 12-05-1980). Los miles van con punto. El RUT no se puede repetir en esta junta."
            titulo = "Importar socios"
        else:
            columnas = [
                {"nombre": "RUT socio titular", "obligatoria": True, "ejemplo": "12.345.678-5"},
                {"nombre": "Nombre", "obligatoria": True, "ejemplo": "Lucas Pérez"},
                {"nombre": "RUT", "obligatoria": False, "ejemplo": "11.111.111-1"},
                {"nombre": "Fecha nacimiento", "obligatoria": False, "ejemplo": "20-08-2010"},
                {"nombre": "Correo", "obligatoria": False, "ejemplo": ""},
                {"nombre": "Teléfono", "obligatoria": False, "ejemplo": ""},
            ]
            intro = "Carga el grupo familiar. Cada fila es un integrante y debe indicar el RUT del socio titular ya registrado."
            ayuda = "Fechas en DD-MM-AAAA. El titular tiene que existir antes. Si el familiar trae RUT, tampoco se duplica."
            titulo = "Importar grupo familiar"
        return render(
            request,
            "admin/vecinos/importar.html",
            {
                "title": titulo,
                "tipo": tipo,
                "resultado": resultado,
                "columnas": columnas,
                "introduccion": intro,
                "ayuda_columnas": ayuda,
                "volver_url": reverse(volver),
                "plantilla_url": (
                    reverse("admin:vecinos_vecino_plantilla")
                    if tipo == "socios"
                    else reverse("admin:vecinos_familiar_plantilla")
                ),
                **self.admin_site.each_context(request),
            },
        )


@admin.register(Vecino)
class VecinoAdmin(ImportacionExcelMixin, JuntaScopedAdminMixin, ModelAdmin):
    list_display = (
        "rut",
        "nombres",
        "apellido_paterno",
        "direccion",
        "cantidad_familiares",
        "activo",
        "junta",
    )
    list_filter = ("activo", "mostrar_cumpleanos", "junta")
    search_fields = (
        "rut",
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        "direccion",
        "grupo_familiar__nombre",
        "grupo_familiar__rut",
    )
    list_editable = ("activo",)
    inlines = [FamiliarInline]
    change_list_template = "admin/vecinos/vecino/change_list.html"
    fieldsets = (
        (
            "Socio titular",
            {
                "fields": (
                    "junta",
                    "rut",
                    "nombres",
                    "apellido_paterno",
                    "apellido_materno",
                    "direccion",
                    "fecha_nacimiento",
                    "email",
                    "telefono",
                    "fecha_ingreso",
                    "activo",
                    "mostrar_cumpleanos",
                )
            },
        ),
    )

    def cantidad_familiares(self, obj):
        return obj.grupo_familiar.count()

    cantidad_familiares.short_description = "Grupo familiar"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("grupo_familiar")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if self._es_plataforma(request):
            return fieldsets
        limpios = []
        for titulo, opts in fieldsets:
            campos = tuple(c for c in opts.get("fields", ()) if c != "junta")
            limpios.append((titulo, {**opts, "fields": campos}))
        return limpios

    def get_list_filter(self, request):
        if self._es_plataforma(request):
            return self.list_filter
        return ("activo", "mostrar_cumpleanos")

    def get_list_display(self, request):
        if self._es_plataforma(request):
            return self.list_display
        return tuple(c for c in self.list_display if c != "junta")

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "plantilla-socios/",
                self.admin_site.admin_view(self.plantilla_socios_vista),
                name="vecinos_vecino_plantilla",
            ),
            path(
                "importar-socios/",
                self.admin_site.admin_view(self.importar_socios_vista),
                name="vecinos_vecino_importar",
            ),
        ]
        return extra + urls

    def plantilla_socios_vista(self, request):
        return self._respuesta_plantilla(plantilla_socios(), "plantilla-socios.xlsx")

    def importar_socios_vista(self, request):
        return self._importar_vista(request, "socios")


@admin.register(Familiar)
class FamiliarAdmin(ImportacionExcelMixin, JuntaScopedAdminMixin, ModelAdmin):
    junta_field = "socio__junta"
    list_display = ("nombre", "rut", "socio", "telefono", "email")
    search_fields = ("nombre", "rut", "socio__nombres", "socio__apellido_paterno", "socio__rut")
    autocomplete_fields = ("socio",)
    list_filter = ("socio__junta",)
    change_list_template = "admin/vecinos/familiar/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "plantilla-familiares/",
                self.admin_site.admin_view(self.plantilla_familiares_vista),
                name="vecinos_familiar_plantilla",
            ),
            path(
                "importar-familiares/",
                self.admin_site.admin_view(self.importar_familiares_vista),
                name="vecinos_familiar_importar",
            ),
        ]
        return extra + urls

    def plantilla_familiares_vista(self, request):
        return self._respuesta_plantilla(plantilla_familiares(), "plantilla-grupo-familiar.xlsx")

    def importar_familiares_vista(self, request):
        return self._importar_vista(request, "familiares")

    def get_list_filter(self, request):
        if self._es_plataforma(request):
            return self.list_filter
        return ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "socio" and not self._es_plataforma(request) and request.user.junta_id:
            kwargs["queryset"] = Vecino.objects.filter(junta=request.user.junta)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Certificado)
class CertificadoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    form = CertificadoAdminForm
    list_display = (
        "codigo",
        "nombre_impreso",
        "rut_impreso",
        "origen",
        "emitido_en",
        "emitido_por",
        "anulado",
        "descargar_pdf",
    )
    list_filter = ("origen", "anulado", "junta")
    search_fields = ("codigo", "nombre_impreso", "rut_impreso", "direccion_impresa")
    readonly_fields = (
        "codigo",
        "contenido_hash",
        "emitido_en",
        "ip_solicitud",
        "origen",
        "emitido_por",
        "descargar_pdf",
    )
    fieldsets = (
        (
            "¿Para quién? (elige socio, familiar, o escribe los datos)",
            {
                "fields": ("junta", "vecino", "familiar", "nombre_impreso", "rut_impreso", "direccion_impresa", "observacion"),
                "description": (
                    "El socio titular puede pedir el PDF en la web con su RUT. "
                    "Un hijo u otro familiar solo lo emite la directiva aquí, a mano o eligiendo el grupo familiar."
                ),
            },
        ),
        (
            "Registro (no se elimina)",
            {"fields": ("codigo", "origen", "emitido_por", "emitido_en", "ip_solicitud", "contenido_hash", "anulado", "descargar_pdf")},
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "<int:object_id>/pdf/",
                self.admin_site.admin_view(self.descargar_pdf_vista),
                name="vecinos_certificado_pdf",
            )
        ]
        return extra + urls

    def descargar_pdf(self, obj):
        if not obj.pk:
            return "—"
        url = reverse("admin:vecinos_certificado_pdf", args=[obj.pk])
        return format_html('<a href="{}">Descargar PDF</a>', url)

    descargar_pdf.short_description = "PDF"

    def descargar_pdf_vista(self, request, object_id):
        certificado = self.get_queryset(request).filter(pk=object_id).first()
        if not certificado:
            raise Http404()
        pdf = pdf_de_certificado(certificado)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="certificado-{certificado.codigo}.pdf"'
        return response

    def get_readonly_fields(self, request, obj=None):
        base = list(self.readonly_fields)
        if obj:
            return base + [
                "junta",
                "vecino",
                "familiar",
                "nombre_impreso",
                "rut_impreso",
                "direccion_impresa",
                "observacion",
            ]
        if not self._es_plataforma(request):
            return base + ["junta"]
        return base

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if self._es_plataforma(request) or obj:
            return fieldsets
        limpios = []
        for titulo, opts in fieldsets:
            campos = tuple(c for c in opts.get("fields", ()) if c != "junta")
            limpios.append((titulo, {**opts, "fields": campos}))
        return limpios

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not self._es_plataforma(request) and request.user.junta_id:
            if db_field.name == "vecino":
                kwargs["queryset"] = Vecino.objects.filter(junta=request.user.junta)
            if db_field.name == "familiar":
                kwargs["queryset"] = Familiar.objects.filter(socio__junta=request.user.junta)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        if self._es_plataforma(request):
            return True
        return request.user.has_perm("vecinos.add_certificado")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return
        if not obj.junta_id:
            obj.junta = request.user.junta
        completar_desde_relaciones(obj)
        creado = crear_certificado(
            junta=obj.junta,
            nombre=obj.nombre_impreso,
            rut=obj.rut_impreso,
            direccion=obj.direccion_impresa,
            vecino=obj.vecino,
            familiar=obj.familiar,
            origen=Certificado.Origen.MANUAL,
            emitido_por=request.user,
            observacion=obj.observacion,
            ip=request.META.get("REMOTE_ADDR"),
        )
        obj.pk = creado.pk
        obj.codigo = creado.codigo
        obj.contenido_hash = creado.contenido_hash
        obj.emitido_en = creado.emitido_en
        obj.origen = creado.origen
        obj.emitido_por = creado.emitido_por
        url = reverse("admin:vecinos_certificado_pdf", args=[creado.pk])
        messages.success(
            request,
            format_html(
                "Certificado {} registrado. No se puede borrar. <a href='{}'>Descargar PDF</a>",
                creado.codigo,
                url,
            ),
        )

    def get_list_filter(self, request):
        if self._es_plataforma(request):
            return self.list_filter
        return ("origen", "anulado")


@admin.register(DisenoCertificado)
class DisenoCertificadoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("junta", "titulo", "mostrar_logo", "mostrar_qr", "abrir_editor")
    fieldsets = (
        ("Identidad visual", {"fields": ("junta", "logo", "mostrar_logo", "titulo")}),
        (
            "Texto con variables",
            {
                "fields": ("cuerpo", "texto_verificacion", "texto_pie"),
                "description": AYUDA_VARIABLES,
            },
        ),
        (
            "Qué datos y dónde va el verificador",
            {
                "fields": (
                    "mostrar_caja_datos",
                    "mostrar_nombre",
                    "mostrar_rut",
                    "mostrar_domicilio",
                    "mostrar_fecha",
                    "mostrar_codigo",
                    "mostrar_qr",
                ),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "<path:object_id>/editor/",
                self.admin_site.admin_view(self.editor_vista),
                name="vecinos_disenocertificado_editor",
            ),
            path(
                "<path:object_id>/pdf-muestra/",
                self.admin_site.admin_view(self.pdf_muestra_vista),
                name="vecinos_disenocertificado_pdf_muestra",
            ),
        ]
        return extra + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("admin:vecinos_disenocertificado_editor", object_id=object_id)

    def abrir_editor(self, obj):
        url = reverse("admin:vecinos_disenocertificado_editor", args=[obj.pk])
        return format_html('<a href="{}">Editor visual del PDF</a>', url)

    abrir_editor.short_description = "Editor visual"

    def editor_vista(self, request, object_id):
        diseno = self.get_queryset(request).filter(pk=object_id).first()
        if not diseno:
            raise Http404()
        if request.method == "POST":
            self._guardar_editor(request, diseno)
            messages.success(request, "Diseño guardado. La previsualización ya usa el nuevo logo y medidas.")
            return redirect("admin:vecinos_disenocertificado_editor", object_id=diseno.pk)

        junta = diseno.junta
        muestra = certificado_muestra(junta)
        ctx = contexto_certificado(muestra)
        logo = diseno.logo if diseno.logo else junta.logo
        return render(
            request,
            "admin/vecinos/diseno_editor.html",
            {
                "diseno": diseno,
                "junta": junta,
                "ctx": ctx,
                "fecha_emision": ctx["fecha.emision"],
                "cuerpo_preview": renderizar(diseno.cuerpo, ctx),
                "verificacion_preview": renderizar(diseno.texto_verificacion, ctx),
                "pie_preview": renderizar(diseno.texto_pie, ctx),
                "logo_url": logo.url if logo else "",
                "ayuda": AYUDA_VARIABLES,
                "pdf_muestra_url": reverse("admin:vecinos_disenocertificado_pdf_muestra", args=[diseno.pk]),
                "title": f"Diseño visual · {junta.nombre}",
                "layout": layout_completo(diseno),
                "bloques": BLOQUES,
                "layout_default": layout_por_defecto(),
            },
        )

    def pdf_muestra_vista(self, request, object_id):
        diseno = self.get_queryset(request).filter(pk=object_id).first()
        if not diseno:
            raise Http404()
        pdf = construir_pdf(certificado_muestra(diseno.junta))
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="certificado-muestra.pdf"'
        return response

    def _guardar_editor(self, request, diseno):
        post = request.POST
        diseno.titulo = post.get("titulo", diseno.titulo)
        diseno.cuerpo = post.get("cuerpo", diseno.cuerpo)
        diseno.texto_verificacion = post.get("texto_verificacion", diseno.texto_verificacion)
        diseno.texto_pie = post.get("texto_pie", diseno.texto_pie)
        diseno.mostrar_logo = post.get("mostrar_logo") == "on"
        diseno.mostrar_caja_datos = post.get("mostrar_caja_datos") == "on"
        diseno.mostrar_nombre = post.get("mostrar_nombre") == "on"
        diseno.mostrar_rut = post.get("mostrar_rut") == "on"
        diseno.mostrar_domicilio = post.get("mostrar_domicilio") == "on"
        diseno.mostrar_fecha = post.get("mostrar_fecha") == "on"
        diseno.mostrar_codigo = post.get("mostrar_codigo") == "on"
        diseno.mostrar_qr = post.get("mostrar_qr") == "on"
        try:
            layout = json.loads(post.get("layout_json") or "{}")
            if isinstance(layout, dict) and layout:
                completo = layout_completo(diseno)
                for clave, bloque in completo.items():
                    if isinstance(layout.get(clave), dict):
                        for k, valor in layout[clave].items():
                            if k in {"x", "y", "w", "h"}:
                                bloque[k] = round(float(valor), 2)
                            elif k in {"z", "font", "zoom", "panX", "panY", "pad", "padL", "radius"}:
                                bloque[k] = float(valor)
                            elif k == "align" and valor in {"left", "center", "right", "justify"}:
                                bloque[k] = valor
                            elif k in {"bg", "color"} and isinstance(valor, str):
                                bloque[k] = valor
                            elif k == "fit":
                                bloque[k] = bool(valor)
                if isinstance(layout.get("pagina"), dict) and isinstance(layout["pagina"].get("bg"), str):
                    completo.setdefault("pagina", {})["bg"] = layout["pagina"]["bg"]
                diseno.layout = completo
                logo = completo.get("logo") or {}
                if logo:
                    dos = Decimal("0.01")
                    diseno.logo_x = Decimal(str(logo.get("x", diseno.logo_x))).quantize(dos)
                    diseno.logo_y = Decimal(str(logo.get("y", diseno.logo_y))).quantize(dos)
                    diseno.logo_ancho = Decimal(str(logo.get("w", diseno.logo_ancho))).quantize(dos)
                    diseno.logo_alto = Decimal(str(logo.get("h", diseno.logo_alto))).quantize(dos)
        except (json.JSONDecodeError, TypeError, ValueError, InvalidOperation):
            pass
        if request.FILES.get("logo"):
            diseno.logo = request.FILES["logo"]
        diseno.save()

    def has_module_permission(self, request):
        return request.user.is_authenticated and self._es_plataforma(request)

    def has_view_permission(self, request, obj=None):
        return self._es_plataforma(request)

    def has_add_permission(self, request):
        return self._es_plataforma(request)

    def has_change_permission(self, request, obj=None):
        return self._es_plataforma(request)

    def has_delete_permission(self, request, obj=None):
        return self._es_plataforma(request)
