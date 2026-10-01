import json
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.contrib import admin, messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from cuentas.admin_mixins import JuntaScopedAdminMixin
from tesoreria.layout import BLOQUES, layout_completo, layout_por_defecto
from tesoreria.models import DisenoComprobante, Movimiento, PagoCuota
from tesoreria.pdf import construir_comprobante, obtener_diseno
from tesoreria.services import (
    MESES_CORTO,
    aplicar_pagos_masivos,
    cuadro_anual,
    nombre_comprobante,
    pagos_del_dia,
    parsear_fecha,
)
from tesoreria.variables import AYUDA_COMPROBANTE, contexto_comprobante, renderizar
from vecinos.models import Vecino


@admin.register(PagoCuota)
class PagoCuotaAdmin(JuntaScopedAdminMixin, ModelAdmin):
    junta_field = "vecino__junta"
    list_display = ("vecino", "mes", "anio", "monto", "pagado_en")
    list_filter = ("anio", "mes")
    search_fields = ("vecino__nombres", "vecino__apellido_paterno", "vecino__rut")
    autocomplete_fields = ("vecino",)
    change_list_template = "admin/tesoreria/pagocuota/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "estado/",
                self.admin_site.admin_view(self.estado_vista),
                name="tesoreria_pagocuota_estado",
            ),
            path(
                "carga-masiva/",
                self.admin_site.admin_view(self.carga_masiva_vista),
                name="tesoreria_pagocuota_carga",
            ),
            path(
                "comprobante/<int:socio_id>/",
                self.admin_site.admin_view(self.comprobante_vista),
                name="tesoreria_pagocuota_comprobante",
            ),
        ]
        return extra + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["estado_url"] = "estado/"
        extra_context["carga_url"] = "carga-masiva/"
        return super().changelist_view(request, extra_context=extra_context)

    def _socios_junta(self, request):
        qs = Vecino.objects.filter(activo=True).select_related("junta").prefetch_related("pagos_cuota")
        if not self._es_plataforma(request) and request.user.junta_id:
            qs = qs.filter(junta=request.user.junta)
        return qs

    def estado_vista(self, request):
        hoy = timezone.localdate()
        try:
            anio = int(request.GET.get("anio") or hoy.year)
        except ValueError:
            anio = hoy.year
        solo_morosos = request.GET.get("morosos") == "1"
        filas = []
        for socio in self._socios_junta(request).order_by("apellido_paterno", "nombres"):
            cuadro = cuadro_anual(socio, anio, hoy)
            if solo_morosos and not cuadro["es_moroso"]:
                continue
            filas.append({"socio": socio, "cuadro": cuadro})
        deuda_total = sum((f["cuadro"]["monto_deuda"] for f in filas), start=0)
        morosos = sum(1 for f in filas if f["cuadro"]["es_moroso"])
        return render(
            request,
            "admin/tesoreria/estado_cuotas.html",
            {
                "filas": filas,
                "anio": anio,
                "anios": range(hoy.year, hoy.year - 6, -1),
                "meses": MESES_CORTO[1:],
                "solo_morosos": solo_morosos,
                "resumen": {
                    "socios": len(filas),
                    "morosos": morosos,
                    "deuda": deuda_total,
                },
                "title": f"Cuotas {anio}",
                **self.admin_site.each_context(request),
            },
        )

    def carga_masiva_vista(self, request):
        hoy = timezone.localdate()
        try:
            anio = int(request.POST.get("anio") or request.GET.get("anio") or hoy.year)
        except ValueError:
            anio = hoy.year
        fecha = parsear_fecha(request.POST.get("fecha") or request.GET.get("fecha"), hoy)
        socios = self._socios_junta(request).order_by("apellido_paterno", "nombres")
        if request.method == "POST":
            cambios = aplicar_pagos_masivos(socios, anio, fecha, request.POST)
            if cambios:
                messages.success(
                    request,
                    f"Se actualizaron {cambios} pagos. El comprobante de cada socio muestra lo pagado el {fecha.strftime('%d-%m-%Y')}.",
                )
            else:
                messages.info(request, "No hubo cambios en los montos.")
            return redirect(f"{reverse('admin:tesoreria_pagocuota_carga')}?anio={anio}&fecha={fecha.isoformat()}")

        filas = []
        for socio in socios:
            cuadro = cuadro_anual(socio, anio, hoy)
            filas.append(
                {
                    "socio": socio,
                    "cuadro": cuadro,
                    "valor": int(cuadro["valor"] or 0) or "",
                }
            )
        diseno_url = ""
        junta = request.user.junta
        if junta:
            diseno = obtener_diseno(junta)
            diseno_url = reverse("admin:tesoreria_disenocomprobante_editor", args=[diseno.pk])
        return render(
            request,
            "admin/tesoreria/carga_masiva.html",
            {
                "filas": filas,
                "anio": anio,
                "fecha": fecha,
                "anios": range(hoy.year + 1, hoy.year - 6, -1),
                "meses": MESES_CORTO[1:],
                "diseno_url": diseno_url,
                "title": "Carga masiva de cuotas",
                **self.admin_site.each_context(request),
            },
        )

    def comprobante_vista(self, request, socio_id):
        socio = get_object_or_404(self._socios_junta(request), pk=socio_id)
        fecha = parsear_fecha(request.GET.get("fecha"), timezone.localdate())
        pagos = pagos_del_dia(socio, fecha)
        pdf = construir_comprobante(socio, fecha, pagos)
        nombre = nombre_comprobante(socio, fecha)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename*=UTF-8''{quote(nombre)}"
        return response

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vecino" and not self._es_plataforma(request) and request.user.junta_id:
            kwargs["queryset"] = Vecino.objects.filter(junta=request.user.junta)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.monto and obj.vecino_id:
            obj.monto = obj.vecino.junta.valor_cuota or 0
        super().save_model(request, obj, form, change)
        if not change:
            Movimiento.objects.get_or_create(
                junta=obj.vecino.junta,
                tipo=Movimiento.Tipo.INGRESO,
                fecha=obj.pagado_en,
                monto=obj.monto,
                detalle=f"Cuota {obj.mes:02d}/{obj.anio} · {obj.vecino.nombre_completo}",
                categoria="cuota",
                socio=obj.vecino,
            )


@admin.register(Movimiento)
class MovimientoAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("fecha", "tipo", "monto", "categoria", "detalle", "socio", "junta")
    list_filter = ("tipo", "categoria", "junta")
    search_fields = ("detalle", "categoria", "socio__nombres", "socio__apellido_paterno")
    autocomplete_fields = ("socio",)
    change_list_template = "admin/tesoreria/movimiento/change_list.html"

    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        ingresos = sum(m.monto for m in qs.filter(tipo=Movimiento.Tipo.INGRESO))
        egresos = sum(m.monto for m in qs.filter(tipo=Movimiento.Tipo.EGRESO))
        extra_context = extra_context or {}
        extra_context["resumen_caja"] = {
            "ingresos": ingresos,
            "egresos": egresos,
            "saldo": ingresos - egresos,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_list_filter(self, request):
        if self._es_plataforma(request):
            return self.list_filter
        return ("tipo", "categoria")

    def get_list_display(self, request):
        if self._es_plataforma(request):
            return self.list_display
        return tuple(c for c in self.list_display if c != "junta")


@admin.register(DisenoComprobante)
class DisenoComprobanteAdmin(JuntaScopedAdminMixin, ModelAdmin):
    list_display = ("junta", "titulo", "mostrar_logo", "abrir_editor")
    fieldsets = (
        ("Identidad visual", {"fields": ("junta", "logo", "mostrar_logo", "titulo")}),
        ("Textos", {"fields": ("cuerpo", "texto_pie"), "description": AYUDA_COMPROBANTE}),
        (
            "Qué mostrar",
            {"fields": ("mostrar_caja_datos", "mostrar_nombre", "mostrar_rut", "mostrar_domicilio", "mostrar_fecha")},
        ),
    )

    def changelist_view(self, request, extra_context=None):
        if request.user.junta_id:
            obtener_diseno(request.user.junta)
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "<path:object_id>/editor/",
                self.admin_site.admin_view(self.editor_vista),
                name="tesoreria_disenocomprobante_editor",
            ),
            path(
                "<path:object_id>/pdf-muestra/",
                self.admin_site.admin_view(self.pdf_muestra_vista),
                name="tesoreria_disenocomprobante_pdf_muestra",
            ),
        ]
        return extra + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("admin:tesoreria_disenocomprobante_editor", object_id=object_id)

    def abrir_editor(self, obj):
        url = reverse("admin:tesoreria_disenocomprobante_editor", args=[obj.pk])
        return format_html('<a href="{}">Editor visual del PDF</a>', url)

    abrir_editor.short_description = "Editor visual"

    def editor_vista(self, request, object_id):
        diseno = self.get_queryset(request).filter(pk=object_id).first()
        if not diseno:
            raise Http404()
        if request.method == "POST":
            self._guardar_editor(request, diseno)
            messages.success(request, "Diseño del comprobante guardado.")
            return redirect("admin:tesoreria_disenocomprobante_editor", object_id=diseno.pk)

        junta = diseno.junta
        socio, fecha, pagos = _muestra_comprobante(junta)
        ctx = contexto_comprobante(socio, fecha, pagos)
        logo = diseno.logo if diseno.logo else junta.logo
        return render(
            request,
            "admin/tesoreria/diseno_editor.html",
            {
                "diseno": diseno,
                "junta": junta,
                "ctx": ctx,
                "cuerpo_preview": renderizar(diseno.cuerpo, ctx),
                "pie_preview": renderizar(diseno.texto_pie, ctx),
                "logo_url": logo.url if logo else "",
                "ayuda": AYUDA_COMPROBANTE,
                "pagos_muestra": pagos,
                "fecha_pago": ctx["fecha.pago"],
                "nombres_bloques": dict(BLOQUES),
                "pdf_muestra_url": reverse("admin:tesoreria_disenocomprobante_pdf_muestra", args=[diseno.pk]),
                "title": f"Diseño del comprobante · {junta.nombre}",
                "layout": layout_completo(diseno),
                "bloques": BLOQUES,
                "layout_default": layout_por_defecto(),
            },
        )

    def pdf_muestra_vista(self, request, object_id):
        diseno = self.get_queryset(request).filter(pk=object_id).first()
        if not diseno:
            raise Http404()
        socio, fecha, pagos = _muestra_comprobante(diseno.junta)
        pdf = construir_comprobante(socio, fecha, pagos)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="comprobante-muestra.pdf"'
        return response

    def _guardar_editor(self, request, diseno):
        post = request.POST
        diseno.titulo = post.get("titulo", diseno.titulo)
        diseno.cuerpo = post.get("cuerpo", diseno.cuerpo)
        diseno.texto_pie = post.get("texto_pie", diseno.texto_pie)
        diseno.mostrar_logo = post.get("mostrar_logo") == "on"
        diseno.mostrar_caja_datos = post.get("mostrar_caja_datos") == "on"
        diseno.mostrar_nombre = post.get("mostrar_nombre") == "on"
        diseno.mostrar_rut = post.get("mostrar_rut") == "on"
        diseno.mostrar_domicilio = post.get("mostrar_domicilio") == "on"
        diseno.mostrar_fecha = post.get("mostrar_fecha") == "on"
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
        except (json.JSONDecodeError, TypeError, ValueError, InvalidOperation):
            pass
        if request.FILES.get("logo"):
            diseno.logo = request.FILES["logo"]
        diseno.save()


def _muestra_comprobante(junta):
    from datetime import date
    from types import SimpleNamespace

    socio = SimpleNamespace(
        junta=junta,
        nombre_completo="María Elena González Rojas",
        rut="11111111-1",
        direccion="Calle Principal 45",
    )
    pagos = [
        SimpleNamespace(mes=8, anio=2026, monto=2000),
        SimpleNamespace(mes=9, anio=2026, monto=2000),
    ]
    return socio, date(2026, 10, 1), pagos
