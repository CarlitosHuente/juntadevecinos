from django.test import TestCase
from django.urls import reverse

from contenido.models import Noticia
from juntas.models import Junta
from vecinos.models import Certificado, Familiar, Vecino


class SitioPublicoTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(
            nombre="Junta de Vecinos Huente",
            slug="huente",
            comuna="Los Vilos",
            activa=True,
        )
        self.vecino = Vecino.objects.create(
            junta=self.junta,
            rut="12345678-5",
            nombres="Juan",
            apellido_paterno="Pérez",
            direccion="Pasaje 1",
            activo=True,
        )
        Noticia.objects.create(
            junta=self.junta,
            titulo="Hola barrio",
            slug="hola-barrio",
            cuerpo="Texto",
            publicada=True,
            destacada=True,
        )

    def test_raiz_redirige_a_huente(self):
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse("home", args=["huente"]))

    def test_home_ok(self):
        respuesta = self.client.get(reverse("home", args=["huente"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Junta de Vecinos Huente")

    def test_certificado_rut_invalido(self):
        respuesta = self.client.post(reverse("certificado", args=["huente"]), {"rut": "12345678-9"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no es válido")

    def test_certificado_pdf_y_verificacion(self):
        respuesta = self.client.post(reverse("certificado", args=["huente"]), {"rut": "12.345.678-5"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        cert = Certificado.objects.get(vecino=self.vecino)
        detalle = self.client.get(reverse("verificar_detalle", args=[cert.codigo]))
        self.assertContains(detalle, "válido")
        self.assertContains(detalle, "Juan Pérez")

    def test_familiar_no_puede_pedir_certificado_en_la_web(self):
        Familiar.objects.create(socio=self.vecino, nombre="Lucas Pérez", rut="33333333-3")
        respuesta = self.client.post(reverse("certificado", args=["huente"]), {"rut": "33333333-3"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "grupo familiar")
        self.assertEqual(Certificado.objects.count(), 0)

    def test_transparencia_ok(self):
        respuesta = self.client.get(reverse("transparencia", args=["huente"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Rendición de gastos")
        self.assertContains(respuesta, "Rendición de actividades")

    def test_en_construccion_cubre_publico_y_deja_admin(self):
        with self.settings(SITIO_EN_CONSTRUCCION=True):
            home = self.client.get(reverse("home", args=["huente"]))
            self.assertContains(home, "Sitio en construcción")
            admin = self.client.get("/admin/login/")
            self.assertEqual(admin.status_code, 200)
            self.assertNotContains(admin, "Sitio en construcción")
