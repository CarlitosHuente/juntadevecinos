from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Noticia(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="noticias",
    )
    titulo = models.CharField("Título", max_length=180)
    slug = models.SlugField("URL", max_length=200, blank=True)
    bajada = models.CharField("Bajada", max_length=255, blank=True)
    cuerpo = models.TextField(
        "Artículo",
        help_text="Cuenta lo que pasó, como en un blog. Separa los párrafos con una línea en blanco.",
    )
    imagen = models.ImageField(
        "Foto de portada",
        upload_to="noticias/",
        blank=True,
        help_text="La foto principal del artículo. Sin foto la noticia casi no se ve en el inicio.",
    )
    destacada = models.BooleanField("Destacada en el carrusel", default=False)
    publicada = models.BooleanField("Publicada", default=True)
    publicada_en = models.DateTimeField("Fecha de publicación", default=timezone.now)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Autor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="noticias",
    )

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        unique_together = ("junta", "slug")
        ordering = ["-publicada_en"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:200]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.titulo

    @property
    def foto_principal(self):
        if self.imagen:
            return self.imagen
        extra = self.fotos.exclude(imagen="").first()
        return extra.imagen if extra else None


class FotoNoticia(models.Model):
    noticia = models.ForeignKey(
        Noticia,
        verbose_name="Noticia",
        on_delete=models.CASCADE,
        related_name="fotos",
    )
    imagen = models.ImageField("Foto", upload_to="noticias/galeria/")
    pie = models.CharField("Pie de foto", max_length=180, blank=True)
    orden = models.PositiveSmallIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Foto de la noticia"
        verbose_name_plural = "Galería de fotos"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return self.pie or f"Foto {self.pk}"


class Evento(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    titulo = models.CharField("Título", max_length=180)
    slug = models.SlugField("URL", max_length=200, blank=True)
    descripcion = models.TextField(
        "Crónica del evento",
        help_text="Cuenta la actividad con detalle. Las fotos van en la galería de abajo.",
    )
    fecha_inicio = models.DateTimeField("Inicio")
    fecha_fin = models.DateTimeField("Término", null=True, blank=True)
    lugar = models.CharField("Lugar", max_length=180, blank=True)
    imagen = models.ImageField(
        "Foto de portada",
        upload_to="eventos/",
        blank=True,
        help_text="La foto principal del evento. Sube más abajo las del día.",
    )
    publicado = models.BooleanField("Publicado", default=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        unique_together = ("junta", "slug")
        ordering = ["fecha_inicio"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:200]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.titulo

    @property
    def foto_principal(self):
        if self.imagen:
            return self.imagen
        extra = self.fotos.exclude(imagen="").first()
        return extra.imagen if extra else None


class FotoEvento(models.Model):
    evento = models.ForeignKey(
        Evento,
        verbose_name="Evento",
        on_delete=models.CASCADE,
        related_name="fotos",
    )
    imagen = models.ImageField("Foto", upload_to="eventos/galeria/")
    pie = models.CharField("Pie de foto", max_length=180, blank=True)
    orden = models.PositiveSmallIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Foto del evento"
        verbose_name_plural = "Galería de fotos"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return self.pie or f"Foto {self.pk}"


class SlideCarrusel(models.Model):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="slides",
    )
    titulo = models.CharField("Título", max_length=160)
    texto = models.CharField("Texto", max_length=255, blank=True)
    imagen = models.ImageField("Imagen", upload_to="carrusel/", blank=True)
    enlace = models.CharField("Enlace interno o URL", max_length=255, blank=True)
    orden = models.PositiveSmallIntegerField("Orden", default=0)
    activo = models.BooleanField("Activo", default=True)
    desde = models.DateField("Visible desde", null=True, blank=True)
    hasta = models.DateField("Visible hasta", null=True, blank=True)

    class Meta:
        verbose_name = "Slide del carrusel"
        verbose_name_plural = "Slides del carrusel"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return self.titulo
