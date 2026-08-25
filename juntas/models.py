from django.db import models


class Junta(models.Model):
    nombre = models.CharField("Nombre", max_length=150)
    slug = models.SlugField("URL", unique=True, help_text="Se usa en la web: /huente/")
    logo = models.ImageField("Logo", upload_to="juntas/logos/", blank=True)
    color_primario = models.CharField("Color primario", max_length=7, default="#2D8A4E")
    color_acento = models.CharField("Color acento", max_length=7, default="#F4C430")
    color_apoyo = models.CharField("Color de apoyo", max_length=7, default="#3A8FCD")
    direccion = models.CharField("Dirección", max_length=255, blank=True)
    comuna = models.CharField("Comuna", max_length=80, blank=True)
    presidente = models.CharField(
        "Presidente/a (certificados)",
        max_length=150,
        blank=True,
        help_text="Nombre que aparece en el certificado de residencia.",
    )
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    email = models.EmailField("Correo", blank=True)
    descripcion = models.TextField("Quiénes somos", blank=True)
    activa = models.BooleanField("Activa", default=True)

    class Meta:
        verbose_name = "Junta de vecinos"
        verbose_name_plural = "Juntas de vecinos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class CargoDirectiva(models.Model):
    junta = models.ForeignKey(
        Junta,
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="cargos",
    )
    cargo = models.CharField("Cargo", max_length=80, help_text="Ej: Presidente/a, Secretario/a, Tesorero/a")
    nombre = models.CharField("Nombre", max_length=150)
    foto = models.ImageField("Foto", upload_to="juntas/directiva/", blank=True)
    orden = models.PositiveSmallIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Integrante de la directiva"
        verbose_name_plural = "Directiva"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return f"{self.cargo}: {self.nombre}"
