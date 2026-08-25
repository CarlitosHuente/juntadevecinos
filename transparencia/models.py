from django.db import models


class RendicionGasto(models.Model):
    class Categoria(models.TextChoices):
        CUOTAS = "cuotas", "Cuotas y aportes"
        SEDE = "sede", "Sede y mantención"
        ACTIVIDADES = "actividades", "Actividades y eventos"
        SERVICIOS = "servicios", "Servicios e insumos"
        OTROS = "otros", "Otros"

    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="gastos",
    )
    fecha = models.DateField("Fecha")
    concepto = models.CharField("Concepto", max_length=180)
    categoria = models.CharField("Categoría", max_length=20, choices=Categoria.choices, default=Categoria.OTROS)
    monto = models.DecimalField("Monto (CLP)", max_digits=12, decimal_places=0)
    descripcion = models.TextField("Detalle", blank=True)
    documento = models.FileField(
        "Boleta, factura o planilla",
        upload_to="transparencia/gastos/",
        blank=True,
        help_text="PDF o imagen. Queda descargable en la web pública.",
    )
    publicada = models.BooleanField("Visible en el sitio", default=True)

    class Meta:
        verbose_name = "Rendición de gasto"
        verbose_name_plural = "Rendiciones de gastos"
        ordering = ["-fecha", "-id"]

    def __str__(self) -> str:
        return f"{self.fecha} · {self.concepto}"


class InformeActividad(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="informes_actividad",
    )
    fecha = models.DateField("Fecha")
    titulo = models.CharField("Actividad", max_length=180)
    descripcion = models.TextField("Qué se hizo y con qué recursos")
    imagen = models.ImageField("Foto", upload_to="transparencia/actividades/", blank=True)
    documento = models.FileField("Acta o informe (PDF)", upload_to="transparencia/actividades/", blank=True)
    publicada = models.BooleanField("Visible en el sitio", default=True)

    class Meta:
        verbose_name = "Rendición de actividad"
        verbose_name_plural = "Rendiciones de actividades"
        ordering = ["-fecha", "-id"]

    def __str__(self) -> str:
        return self.titulo
