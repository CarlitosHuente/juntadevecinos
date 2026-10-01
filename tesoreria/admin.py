from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from unfold.admin import ModelAdmin

from cuentas.admin_mixins import JuntaScopedAdminMixin
from tesoreria.models import Movimiento, PagoCuota
from tesoreria.services import MESES_CORTO, cuadro_anual
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
            )
        ]
        return extra + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["estado_url"] = "estado/"
        return super().changelist_view(request, extra_context=extra_context)

    def estado_vista(self, request):
        hoy = timezone.localdate()
        try:
            anio = int(request.GET.get("anio") or hoy.year)
        except ValueError:
            anio = hoy.year
        solo_morosos = request.GET.get("morosos") == "1"
        qs = Vecino.objects.filter(activo=True).select_related("junta").prefetch_related("pagos_cuota")
        if not self._es_plataforma(request) and request.user.junta_id:
            qs = qs.filter(junta=request.user.junta)
        filas = []
        for socio in qs.order_by("apellido_paterno", "nombres"):
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
