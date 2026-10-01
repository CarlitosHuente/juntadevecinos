from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import Rol
from juntas.models import Junta


class RecorteImagenAdminTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(nombre="Huente", slug="huente-recorte", activa=True)
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="dir_recorte",
            password="huente1234",
            junta=self.junta,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )

    def test_slide_muestra_editor_de_recorte(self):
        self.client.force_login(self.directiva)
        respuesta = self.client.get(reverse("admin:contenido_slidecarrusel_add"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "recorte-imagen.js")
        self.assertContains(respuesta, "data-recorte")
        self.assertContains(respuesta, "Así se verá el slide")
        self.assertContains(respuesta, "Elegir imagen")
        self.assertContains(respuesta, 'for="id_imagen"')
        self.assertContains(respuesta, "Pulsa la foto para moverla")

    def test_noticia_y_evento_tienen_recorte(self):
        self.client.force_login(self.directiva)
        noticia = self.client.get(reverse("admin:contenido_noticia_add"))
        evento = self.client.get(reverse("admin:contenido_evento_add"))
        self.assertContains(noticia, "data-recorte")
        self.assertContains(evento, "data-recorte")
