from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from vecinos.rut import normalizar_rut, validar_rut


def _validar_rut_campo(valor: str) -> None:
    if not validar_rut(valor):
        raise ValidationError("RUT chileno inválido.")


class Vecino(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="vecinos",
    )
    rut = models.CharField("RUT", max_length=12, validators=[_validar_rut_campo])
    nombres = models.CharField("Nombres", max_length=120)
    apellido_paterno = models.CharField("Apellido paterno", max_length=80)
    apellido_materno = models.CharField("Apellido materno", max_length=80, blank=True)
    direccion = models.CharField("Dirección", max_length=255)
    fecha_nacimiento = models.DateField("Fecha de nacimiento", null=True, blank=True)
    email = models.EmailField("Correo", blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    activo = models.BooleanField("Vigente", default=True)
    mostrar_cumpleanos = models.BooleanField(
        "Mostrar cumpleaños en el home",
        default=False,
        help_text="Solo se publica el nombre de pila y la inicial del apellido.",
    )
    fecha_ingreso = models.DateField("Fecha de ingreso", default=timezone.localdate)

    class Meta:
        verbose_name = "Vecino"
        verbose_name_plural = "Vecinos"
        unique_together = ("junta", "rut")
        ordering = ["apellido_paterno", "nombres"]

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.rut})"

    @property
    def nombre_completo(self) -> str:
        partes = [self.nombres, self.apellido_paterno, self.apellido_materno]
        return " ".join(p for p in partes if p)

    @property
    def nombre_publico_cumple(self) -> str:
        inicial = f"{self.apellido_paterno[:1]}." if self.apellido_paterno else ""
        return f"{self.nombres.split()[0]} {inicial}".strip()


class Certificado(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="certificados",
    )
    vecino = models.ForeignKey(
        Vecino,
        verbose_name="Vecino",
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    codigo = models.CharField("Código de verificación", max_length=20, unique=True, db_index=True)
    contenido_hash = models.CharField("Huella del contenido", max_length=64)
    emitido_en = models.DateTimeField("Emitido", auto_now_add=True)
    anulado = models.BooleanField("Anulado", default=False)
    ip_solicitud = models.GenericIPAddressField("IP de solicitud", null=True, blank=True)

    class Meta:
        verbose_name = "Certificado de residencia"
        verbose_name_plural = "Certificados de residencia"
        ordering = ["-emitido_en"]

    def __str__(self) -> str:
        return self.codigo
