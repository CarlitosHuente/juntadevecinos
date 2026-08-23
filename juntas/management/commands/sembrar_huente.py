from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from contenido.models import Evento, Noticia, SlideCarrusel
from cuentas.roles import Rol
from juntas.models import Junta
from vecinos.models import Vecino

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Crea la junta Huente, datos de ejemplo y un superusuario local."

    def handle(self, *args, **options):
        junta, _ = Junta.objects.update_or_create(
            slug="huente",
            defaults={
                "nombre": "Junta de Vecinos Huente",
                "comuna": "Los Vilos",
                "direccion": "Sede comunitaria Huente",
                "presidente": "Directiva Huente",
                "telefono": "+56 9 0000 0000",
                "email": "contacto@juntahuente.cl",
                "descripcion": (
                    "Somos la Junta de Vecinos de Huente. Este sitio informa a la comunidad, "
                    "comparte lo que hacemos y permite emitir certificados de residencia "
                    "con código de verificación."
                ),
                "color_primario": "#2D8A4E",
                "color_acento": "#F4C430",
                "color_apoyo": "#3A8FCD",
                "activa": True,
            },
        )

        if not Usuario.objects.filter(username="admin").exists():
            Usuario.objects.create_superuser(
                username="admin",
                email="admin@juntahuente.cl",
                password="admin1234",
                first_name="Admin",
                last_name="Huente",
                rol=Rol.SUPERADMIN,
                is_staff=True,
            )
            self.stdout.write("Usuario admin / admin1234 creado (cámbialo en producción).")

        for username, rol, nombre in (
            ("comunicador", Rol.COMUNICADOR, "Camila"),
            ("secretario", Rol.SECRETARIO, "Sergio"),
            ("directiva", Rol.DIRECTIVA, "Diana"),
        ):
            if not Usuario.objects.filter(username=username).exists():
                Usuario.objects.create_user(
                    username=username,
                    email=f"{username}@juntahuente.cl",
                    password="huente1234",
                    first_name=nombre,
                    last_name="Huente",
                    junta=junta,
                    rol=rol,
                    is_staff=True,
                )

        hoy = timezone.localdate()
        vecinos = (
            {
                "rut": "12345678-5",
                "nombres": "Juan Andrés",
                "apellido_paterno": "Pérez",
                "apellido_materno": "Soto",
                "direccion": "Pasaje Los Aromos 120",
                "fecha_nacimiento": hoy,
                "mostrar_cumpleanos": True,
            },
            {
                "rut": "11111111-1",
                "nombres": "María Elena",
                "apellido_paterno": "González",
                "apellido_materno": "Rojas",
                "direccion": "Calle Principal 45",
                "fecha_nacimiento": hoy.replace(year=1984, month=3, day=12),
                "mostrar_cumpleanos": False,
            },
            {
                "rut": "22222222-2",
                "nombres": "Pedro",
                "apellido_paterno": "Muñoz",
                "apellido_materno": "",
                "direccion": "Camino Costero 8",
                "fecha_nacimiento": hoy + timedelta(days=3),
                "mostrar_cumpleanos": True,
            },
        )
        for data in vecinos:
            Vecino.objects.update_or_create(
                junta=junta,
                rut=data["rut"],
                defaults=data,
            )

        Noticia.objects.update_or_create(
            junta=junta,
            slug="inauguracion-sede",
            defaults={
                "titulo": "Reabrimos la sede con las puertas abiertas",
                "bajada": "Un sábado de pintura, mate y vecinos de todas las edades.",
                "cuerpo": (
                    "La directiva agradece a quienes llegaron a dejar la sede más linda. "
                    "Pronto anunciaremos talleres y una feria de barrio."
                ),
                "destacada": True,
                "publicada": True,
                "publicada_en": timezone.now(),
            },
        )
        Noticia.objects.update_or_create(
            junta=junta,
            slug="recoleccion-reciclaje",
            defaults={
                "titulo": "Nueva jornada de reciclaje",
                "bajada": "Vidrio, cartón y tapitas: trae lo que tengas en casa.",
                "cuerpo": "El punto de acopio estará en la sede el próximo fin de semana.",
                "destacada": False,
                "publicada": True,
            },
        )

        Evento.objects.update_or_create(
            junta=junta,
            slug="bingo-familiar",
            defaults={
                "titulo": "Bingo familiar",
                "descripcion": "Tarde de bingo para juntar fondos de la sede. Hay premios del barrio.",
                "fecha_inicio": timezone.now() + timedelta(days=10, hours=3),
                "lugar": "Sede comunitaria",
                "publicado": True,
            },
        )

        SlideCarrusel.objects.update_or_create(
            junta=junta,
            titulo="Tu certificado, en un minuto",
            defaults={
                "texto": "Ingresa tu RUT y descarga un PDF con QR para que nadie lo adultere.",
                "enlace": "/huente/certificado/",
                "orden": 1,
                "activo": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Junta Huente y datos de ejemplo listos."))
