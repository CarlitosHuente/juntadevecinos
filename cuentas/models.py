from django.contrib.auth.models import AbstractUser
from django.db import models

from cuentas.roles import Rol


class Usuario(AbstractUser):
    junta = models.ForeignKey(
        "juntas.Junta",
        verbose_name="Junta",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
        help_text="Vacío solo para superadmin de la plataforma.",
    )
    rol = models.CharField("Rol", max_length=20, choices=Rol.CHOICES, default=Rol.COMUNICADOR)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def es_superadmin(self) -> bool:
        return self.is_superuser or self.rol == Rol.SUPERADMIN
