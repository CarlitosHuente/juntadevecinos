from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from contenido.models import Evento, FotoNoticia, Noticia
from juntas.models import Junta
from vecinos.models import Certificado, Familiar, Vecino


class SitioPublicoTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(
            nombre="Junta de Vecinos Huente",
            slug="huentelauquen",
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

    def test_raiz_redirige_a_huentelauquen(self):
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, "/huentelauquen/")

    def test_huente_redirige_a_huentelauquen(self):
        respuesta = self.client.get("/huente/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, "/huentelauquen/")

    def test_home_ok(self):
        respuesta = self.client.get(reverse("home", args=["huentelauquen"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Junta de Vecinos Huente")
        self.assertNotContains(respuesta, "cdn.tailwindcss.com")

    def test_carrusel_usa_foto_de_noticia_destacada(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        lienzo = BytesIO()
        Image.new("RGB", (12, 8), "green").save(lienzo, format="PNG")
        Noticia.objects.filter(slug="hola-barrio").update(destacada=True)
        noticia = Noticia.objects.get(slug="hola-barrio")
        noticia.imagen.save("portada.png", SimpleUploadedFile("portada.png", lienzo.getvalue(), content_type="image/png"))
        home = self.client.get(reverse("home", args=["huentelauquen"]))
        self.assertContains(home, noticia.imagen.url)

    def test_certificado_rut_invalido(self):
        respuesta = self.client.post(reverse("certificado", args=["huentelauquen"]), {"rut": "12345678-9"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no es válido")

    def test_certificado_pdf_y_verificacion(self):
        respuesta = self.client.post(reverse("certificado", args=["huentelauquen"]), {"rut": "12.345.678-5"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        cert = Certificado.objects.get(vecino=self.vecino)
        detalle = self.client.get(reverse("verificar_detalle", args=[cert.codigo]))
        self.assertContains(detalle, "válido")
        self.assertContains(detalle, "Juan Pérez")

    def test_certificado_bloqueado_si_hay_deuda(self):
        from tesoreria.models import PagoCuota

        self.junta.valor_cuota = 1000
        self.junta.certificado_con_deuda = False
        self.junta.save()
        self.vecino.fecha_ingreso = timezone.localdate().replace(day=1)
        self.vecino.save()
        respuesta = self.client.post(reverse("certificado", args=["huentelauquen"]), {"rut": "12.345.678-5"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "cuotas impagas")
        self.assertEqual(Certificado.objects.count(), 0)
        PagoCuota.objects.create(
            vecino=self.vecino,
            anio=timezone.localdate().year,
            mes=timezone.localdate().month,
            monto=1000,
        )
        ok = self.client.post(reverse("certificado", args=["huentelauquen"]), {"rut": "12.345.678-5"})
        self.assertEqual(ok["Content-Type"], "application/pdf")

    def test_familiar_no_puede_pedir_certificado_en_la_web(self):
        Familiar.objects.create(socio=self.vecino, nombre="Lucas Pérez", rut="33333333-3")
        respuesta = self.client.post(reverse("certificado", args=["huentelauquen"]), {"rut": "33333333-3"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "grupo familiar")
        self.assertEqual(Certificado.objects.count(), 0)

    def test_transparencia_ok(self):
        respuesta = self.client.get(reverse("transparencia", args=["huentelauquen"]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Rendición de gastos")
        self.assertContains(respuesta, "Rendición de actividades")

    def test_en_construccion_cubre_publico_y_deja_admin(self):
        with self.settings(SITIO_EN_CONSTRUCCION=True):
            home = self.client.get("/huentelauquen/")
            self.assertContains(home, "Sitio en construcción")
            raiz = self.client.get("/")
            self.assertEqual(raiz.status_code, 302)
            self.assertEqual(raiz.url, "/huentelauquen/")
            admin = self.client.get("/admin/login/")
            self.assertEqual(admin.status_code, 200)
            self.assertNotContains(admin, "Sitio en construcción")

    def test_noticia_muestra_galeria(self):
        noticia = Noticia.objects.get(slug="hola-barrio")
        lienzo = BytesIO()
        Image.new("RGB", (8, 8), "green").save(lienzo, format="PNG")
        png = SimpleUploadedFile("bingo.png", lienzo.getvalue(), content_type="image/png")
        FotoNoticia.objects.create(noticia=noticia, imagen=png, pie="Vecinos en el bingo")
        detalle = self.client.get(reverse("noticia_detalle", args=["huentelauquen", "hola-barrio"]))
        self.assertContains(detalle, "Fotografías")
        self.assertContains(detalle, "Vecinos en el bingo")

    def test_eventos_muestran_espacio_para_foto(self):
        Evento.objects.create(
            junta=self.junta,
            titulo="Bingo de invierno",
            slug="bingo-invierno",
            descripcion="Tarde comunitaria",
            fecha_inicio=timezone.now(),
            publicado=True,
        )
        lista = self.client.get(reverse("eventos_lista", args=["huentelauquen"]))
        self.assertContains(lista, "Bingo de invierno")
        self.assertContains(lista, "Sin foto aún")
