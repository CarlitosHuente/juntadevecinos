from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from contenido.models import Evento, Noticia, SlideCarrusel
from cuentas.roles import Rol
from juntas.models import CargoDirectiva, Junta
from transparencia.models import InformeActividad, RendicionGasto
from vecinos.models import DisenoCertificado, Familiar, Vecino

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
        titulares = {}
        for data in vecinos:
            socio, _ = Vecino.objects.update_or_create(
                junta=junta,
                rut=data["rut"],
                defaults=data,
            )
            titulares[data["rut"]] = socio

        juan = titulares["12345678-5"]
        Familiar.objects.update_or_create(
            socio=juan,
            nombre="Carla Pérez",
            defaults={
                "rut": "33333333-3",
                "fecha_nacimiento": hoy.replace(year=1990, month=5, day=4),
                "email": "carla@example.com",
                "telefono": "+56 9 1111 1111",
            },
        )
        Familiar.objects.update_or_create(
            socio=juan,
            nombre="Lucas Pérez",
            defaults={"fecha_nacimiento": hoy.replace(year=2015, month=8, day=20)},
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

        for orden, cargo, nombre in (
            (1, "Presidente/a", "Directiva Huente"),
            (2, "Secretario/a", "Sergio Huente"),
            (3, "Tesorero/a", "Ana Huente"),
        ):
            CargoDirectiva.objects.update_or_create(
                junta=junta,
                cargo=cargo,
                defaults={"nombre": nombre, "orden": orden},
            )

        RendicionGasto.objects.update_or_create(
            junta=junta,
            concepto="Materiales para pintar la sede",
            defaults={
                "fecha": hoy.replace(day=min(hoy.day, 28)),
                "categoria": RendicionGasto.Categoria.SEDE,
                "monto": 85000,
                "descripcion": "Pintura, rodillos y protección de piso.",
                "publicada": True,
            },
        )
        RendicionGasto.objects.update_or_create(
            junta=junta,
            concepto="Bingo familiar — premios",
            defaults={
                "fecha": hoy,
                "categoria": RendicionGasto.Categoria.ACTIVIDADES,
                "monto": 42000,
                "descripcion": "Canastas y premios donados en parte por el comercio local.",
                "publicada": True,
            },
        )
        InformeActividad.objects.update_or_create(
            junta=junta,
            titulo="Jornada de pintura de la sede",
            defaults={
                "fecha": hoy,
                "descripcion": "Vecinos y directiva pintaron la sede. Se usaron $85.000 en materiales, con boletas que se cargarán en esta sección.",
                "publicada": True,
            },
        )
        DisenoCertificado.objects.get_or_create(junta=junta)

        self.stdout.write(self.style.SUCCESS("Junta Huente y datos de ejemplo listos."))
