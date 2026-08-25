from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from vecinos.layout import layout_por_defecto
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
        verbose_name = "Socio titular"
        verbose_name_plural = "Socios titulares"
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


class Familiar(models.Model):
    socio = models.ForeignKey(
        Vecino,
        verbose_name="Socio titular",
        on_delete=models.CASCADE,
        related_name="grupo_familiar",
    )
    nombre = models.CharField("Nombre", max_length=150)
    rut = models.CharField("RUT", max_length=12, blank=True)
    fecha_nacimiento = models.DateField("Fecha de nacimiento", null=True, blank=True)
    email = models.EmailField("Correo", blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)

    class Meta:
        verbose_name = "Integrante del grupo familiar"
        verbose_name_plural = "Grupo familiar"
        ordering = ["id"]

    def clean(self):
        super().clean()
        if self.rut:
            if not validar_rut(self.rut):
                raise ValidationError({"rut": "RUT chileno inválido."})
            self.rut = normalizar_rut(self.rut)

    def save(self, *args, **kwargs):
        if self.rut:
            self.rut = normalizar_rut(self.rut)
        else:
            self.rut = ""
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nombre


class Certificado(models.Model):
    class Origen(models.TextChoices):
        WEB_RUT = "web_rut", "Solicitud web (socio titular)"
        MANUAL = "manual", "Emisión de la directiva"

    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    vecino = models.ForeignKey(
        Vecino,
        verbose_name="Socio titular (si aplica)",
        on_delete=models.PROTECT,
        related_name="certificados",
        null=True,
        blank=True,
    )
    familiar = models.ForeignKey(
        Familiar,
        verbose_name="Integrante del grupo familiar",
        on_delete=models.PROTECT,
        related_name="certificados",
        null=True,
        blank=True,
    )
    nombre_impreso = models.CharField("Nombre en el certificado", max_length=180, default="")
    rut_impreso = models.CharField("RUT en el certificado", max_length=12, blank=True)
    direccion_impresa = models.CharField("Domicilio en el certificado", max_length=255, default="")
    origen = models.CharField("Origen", max_length=20, choices=Origen.choices, default=Origen.WEB_RUT)
    emitido_por = models.ForeignKey(
        "cuentas.Usuario",
        verbose_name="Emitido por",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="certificados_emitidos",
    )
    observacion = models.CharField("Observación interna", max_length=255, blank=True)
    codigo = models.CharField("Código de verificación", max_length=20, unique=True, db_index=True)
    contenido_hash = models.CharField("Huella del contenido", max_length=64)
    emitido_en = models.DateTimeField("Emitido", auto_now_add=True)
    anulado = models.BooleanField("Anulado", default=False)
    ip_solicitud = models.GenericIPAddressField("IP de solicitud", null=True, blank=True)

    class Meta:
        verbose_name = "Certificado emitido"
        verbose_name_plural = "Certificados emitidos (registro)"
        ordering = ["-emitido_en"]

    def __str__(self) -> str:
        return self.codigo

    def delete(self, using=None, keep_parents=False):
        raise ValidationError("Los certificados no se eliminan. Anúlelos para conservar la trazabilidad.")


CUERPO_CERTIFICADO_DEFAULT = (
    "La <<junta.nombre>> certifica que <<nombre.socio>>, RUT <<rut.socio>>, "
    "reside en <<domicilio>><<comuna.frase>>, y se encuentra registrado(a) "
    "como integrante vigente de esta organización. "
    "Documento emitido el <<fecha.emision>> bajo la presidencia de <<presidente>>."
)

AYUDA_VARIABLES = (
    "Variables: <<nombre.socio>> o <<nombre>>, <<rut.socio>> o <<rut>>, "
    "<<domicilio>>, <<junta.nombre>>, <<junta.comuna>>, <<junta.direccion>>, "
    "<<presidente>>, <<fecha.emision>>, <<codigo>>, <<socio.titular>>, <<comuna.frase>>."
)


class DisenoCertificado(models.Model):
    junta = models.OneToOneField(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.CASCADE,
        related_name="diseno_certificado",
    )
    logo = models.ImageField(
        "Logo del certificado",
        upload_to="certificados/diseno/",
        blank=True,
        help_text="Si lo dejas vacío se usa el logo de la junta.",
    )
    mostrar_logo = models.BooleanField("Mostrar logo", default=True)
    logo_x = models.DecimalField("Logo X (cm desde la izquierda)", max_digits=5, decimal_places=2, default="1.60")
    logo_y = models.DecimalField("Logo Y (cm desde arriba)", max_digits=5, decimal_places=2, default="0.95")
    logo_ancho = models.DecimalField("Ancho del logo (cm)", max_digits=5, decimal_places=2, default="2.20")
    logo_alto = models.DecimalField("Alto del logo (cm)", max_digits=5, decimal_places=2, default="2.20")
    titulo = models.CharField("Título", max_length=120, default="CERTIFICADO DE RESIDENCIA")
    cuerpo = models.TextField("Texto del certificado", default=CUERPO_CERTIFICADO_DEFAULT, help_text=AYUDA_VARIABLES)
    mostrar_caja_datos = models.BooleanField("Mostrar caja de datos", default=True)
    mostrar_nombre = models.BooleanField("Caja: nombre", default=True)
    mostrar_rut = models.BooleanField("Caja: RUT", default=True)
    mostrar_domicilio = models.BooleanField("Caja: domicilio", default=True)
    mostrar_fecha = models.BooleanField("Caja: fecha de emisión", default=True)
    mostrar_codigo = models.BooleanField("Caja: código de verificación", default=True)
    mostrar_qr = models.BooleanField("Mostrar código QR", default=True)
    texto_verificacion = models.TextField(
        "Texto junto al verificador",
        default=(
            "Verifique este documento en el sitio de la junta con el código <<codigo>> "
            "o escaneando el QR. Si el PDF fue alterado, el verificador mostrará los datos oficiales."
        ),
        help_text="Puedes usar <<codigo>>. El QR se dibuja al lado de la caja de datos.",
    )
    texto_pie = models.CharField(
        "Pie de página",
        max_length=255,
        blank=True,
        default="Huella: <<huella>> · <<url.verificacion>>",
        help_text="Variables extra: <<huella>>, <<url.verificacion>>, <<codigo>>.",
    )
    layout = models.JSONField("Posición de cada bloque", default=layout_por_defecto, blank=True)

    class Meta:
        verbose_name = "Diseño de certificado"
        verbose_name_plural = "Diseño de certificados"

    def __str__(self) -> str:
        return f"Diseño · {self.junta.nombre}"
