from django.contrib.auth.models import AbstractUser, Group
from django.db import models

from cuentas.roles import Rol, agregar_grupo_inicial, es_plataforma


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
    rol = models.CharField("Grupo / rol", max_length=20, choices=Rol.CHOICES, default=Rol.COMUNICADOR)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def es_superadmin(self) -> bool:
        return es_plataforma(self)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        agregar_grupo_inicial(self)


class GrupoRol(Group):
    class Meta:
        proxy = True
        app_label = "cuentas"
        verbose_name = "Grupo / rol"
        verbose_name_plural = "Grupos / roles"


class PermisoGrupo(models.Model):
    grupo = models.OneToOneField(
        Group,
        verbose_name="Grupo",
        on_delete=models.CASCADE,
        related_name="permisos_panel",
    )
    juntas = models.BooleanField("Junta (sede, logo, colores)", default=False)
    cuentas = models.BooleanField("Usuarios y grupos", default=False)
    vecinos = models.BooleanField("Socios y certificados", default=False)
    contenido = models.BooleanField("Noticias, eventos y slides", default=False)
    transparencia = models.BooleanField("Transparencia", default=False)
    tesoreria = models.BooleanField("Tesorería y cuotas", default=False)

    class Meta:
        verbose_name = "Permisos del grupo"
        verbose_name_plural = "Permisos de grupos"

    def __str__(self) -> str:
        return f"Permisos · {self.grupo.name}"

    def modulos(self) -> set[str]:
        return {
            campo
            for campo in ("juntas", "cuentas", "vecinos", "contenido", "transparencia", "tesoreria")
            if getattr(self, campo)
        }
