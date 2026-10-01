from django.db import models
from django.utils import timezone

from tesoreria.layout import layout_por_defecto
from tesoreria.variables import CUERPO_COMPROBANTE_DEFAULT, PIE_COMPROBANTE_DEFAULT


class PagoCuota(models.Model):
    vecino = models.ForeignKey(
        "vecinos.Vecino",
        verbose_name="Socio titular",
        on_delete=models.CASCADE,
        related_name="pagos_cuota",
    )
    anio = models.PositiveSmallIntegerField("Año")
    mes = models.PositiveSmallIntegerField("Mes")
    monto = models.DecimalField("Monto", max_digits=12, decimal_places=0)
    pagado_en = models.DateField("Fecha de pago", default=timezone.localdate)
    observacion = models.CharField("Nota", max_length=180, blank=True)

    class Meta:
        verbose_name = "Pago de cuota"
        verbose_name_plural = "Pagos de cuotas"
        unique_together = ("vecino", "anio", "mes")
        ordering = ["-anio", "-mes", "vecino"]

    def __str__(self) -> str:
        return f"{self.vecino} · {self.mes:02d}/{self.anio}"


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        EGRESO = "egreso", "Egreso"

    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    tipo = models.CharField("Tipo", max_length=10, choices=Tipo.choices)
    fecha = models.DateField("Fecha", default=timezone.localdate)
    monto = models.DecimalField("Monto", max_digits=12, decimal_places=0)
    detalle = models.CharField("Detalle", max_length=255)
    categoria = models.CharField(
        "Categoría",
        max_length=80,
        blank=True,
        help_text="Ej: cuota, bingos, luz, aseo, materiales.",
    )
    socio = models.ForeignKey(
        "vecinos.Vecino",
        verbose_name="Socio (si aplica)",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
    )

    class Meta:
        verbose_name = "Ingreso o egreso"
        verbose_name_plural = "Ingresos y egresos"
        ordering = ["-fecha", "-id"]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} · {self.monto} · {self.detalle}"


class DisenoComprobante(models.Model):
    junta = models.OneToOneField(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="diseno_comprobante",
    )
    logo = models.ImageField(
        "Logo del comprobante",
        upload_to="comprobantes/diseno/",
        blank=True,
        help_text="Si lo dejas vacío se usa el logo de la junta.",
    )
    mostrar_logo = models.BooleanField("Mostrar logo", default=True)
    titulo = models.CharField("Título", max_length=120, default="Comprobante de pago")
    cuerpo = models.TextField("Subtítulo", default=CUERPO_COMPROBANTE_DEFAULT)
    texto_pie = models.TextField("Pie de página", default=PIE_COMPROBANTE_DEFAULT)
    mostrar_caja_datos = models.BooleanField("Mostrar datos del socio", default=True)
    mostrar_nombre = models.BooleanField("Caja: nombre", default=True)
    mostrar_rut = models.BooleanField("Caja: RUT", default=True)
    mostrar_domicilio = models.BooleanField("Caja: domicilio", default=True)
    mostrar_fecha = models.BooleanField("Caja: fecha", default=True)
    layout = models.JSONField("Posición de cada bloque", default=layout_por_defecto, blank=True)

    class Meta:
        verbose_name = "Diseño de comprobante"
        verbose_name_plural = "Diseño de comprobantes"

    def __str__(self) -> str:
        return f"Comprobante · {self.junta.nombre}"
