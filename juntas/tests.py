from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import Rol
from juntas.models import Junta


class JuntaAdminTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(nombre="Huente", slug="huente-admin", activa=True)
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="dir_junta",
            password="huente1234",
            junta=self.junta,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )

    def test_directiva_abre_ficha_de_su_junta(self):
        self.client.force_login(self.directiva)
        respuesta = self.client.get(reverse("admin:juntas_junta_change", args=[self.junta.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Tesorería y certificados")
        self.assertContains(respuesta, "Directiva")
        self.assertContains(respuesta, "color-paleta")
        self.assertContains(respuesta, 'type="color"')
        self.assertContains(respuesta, "#2D8A4E")
