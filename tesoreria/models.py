from django.db import models
from django.utils import timezone


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
