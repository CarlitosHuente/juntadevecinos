from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import Rol
from juntas.models import Junta
from vecinos.models import Familiar, Vecino
from vecinos.rut import normalizar_rut, validar_rut


class RutTests(TestCase):
    def test_normaliza_puntos_y_mayusculas(self):
        self.assertEqual(normalizar_rut("12.345.678-k"), "12345678-K")

    def test_rut_validos(self):
        self.assertTrue(validar_rut("12.345.678-5"))
        self.assertTrue(validar_rut("11111111-1"))
        self.assertTrue(validar_rut("22222222-2"))

    def test_rut_invalido(self):
        self.assertFalse(validar_rut("12345678-9"))
        self.assertFalse(validar_rut("abc"))
        self.assertFalse(validar_rut(""))


class GrupoFamiliarTests(TestCase):
    def setUp(self):
        self.huente = Junta.objects.create(nombre="Huente", slug="huente", activa=True)
        self.otra = Junta.objects.create(nombre="Otra", slug="otra", activa=True)
        self.socio = Vecino.objects.create(
            junta=self.huente,
            rut="12345678-5",
            nombres="Juan",
            apellido_paterno="Pérez",
            direccion="Pasaje 1",
        )
        Vecino.objects.create(
            junta=self.otra,
            rut="22222222-2",
            nombres="Otra",
            apellido_paterno="Junta",
            direccion="Calle 2",
        )
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="directiva_test",
            password="huente1234",
            junta=self.huente,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )

    def test_familiar_solo_nombre_obligatorio(self):
        familiar = Familiar(socio=self.socio, nombre="Lucas Pérez")
        familiar.full_clean()
        familiar.save()
        self.assertEqual(self.socio.grupo_familiar.count(), 1)

    def test_familiar_rut_invalido(self):
        familiar = Familiar(socio=self.socio, nombre="Ana", rut="12345678-9")
        with self.assertRaises(ValidationError):
            familiar.full_clean()

    def test_directiva_no_ve_socios_de_otra_junta(self):
        self.client.force_login(self.directiva)
        respuesta = self.client.get(reverse("admin:vecinos_vecino_changelist"))
        self.assertContains(respuesta, "Juan")
        self.assertNotContains(respuesta, "22222222-2")


class CertificadoTrazabilidadTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(nombre="Huente", slug="huente", activa=True)
        self.socio = Vecino.objects.create(
            junta=self.junta,
            rut="12345678-5",
            nombres="Juan",
            apellido_paterno="Pérez",
            direccion="Pasaje 1",
        )
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="dir_cert",
            password="huente1234",
            junta=self.junta,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )
        self.comunicador = Usuario.objects.create_user(
            username="com_cert",
            password="huente1234",
            junta=self.junta,
            rol=Rol.COMUNICADOR,
            is_staff=True,
        )

    def test_directiva_emite_manual_y_no_se_borra(self):
        from vecinos.models import Certificado
        from vecinos.services import crear_certificado

        cert = crear_certificado(
            junta=self.junta,
            nombre="Lucas Pérez",
            rut="",
            direccion="Pasaje 1",
            vecino=self.socio,
            origen=Certificado.Origen.MANUAL,
            emitido_por=self.directiva,
        )
        self.assertTrue(cert.codigo)
        with self.assertRaises(ValidationError):
            cert.delete()
        self.assertTrue(Certificado.objects.filter(pk=cert.pk).exists())

    def test_directiva_ve_registro_y_comunicador_no_emite(self):
        self.client.force_login(self.directiva)
        lista = self.client.get(reverse("admin:vecinos_certificado_changelist"))
        self.assertEqual(lista.status_code, 200)
        alta = self.client.get(reverse("admin:vecinos_certificado_add"))
        self.assertEqual(alta.status_code, 200)

        self.client.force_login(self.comunicador)
        alta_com = self.client.get(reverse("admin:vecinos_certificado_add"))
        self.assertEqual(alta_com.status_code, 403)

    def test_solo_superadmin_ve_diseno(self):
        self.client.force_login(self.directiva)
        diseno = self.client.get(reverse("admin:vecinos_disenocertificado_changelist"))
        self.assertEqual(diseno.status_code, 403)

    def test_superadmin_abre_editor_visual(self):
        from vecinos.models import DisenoCertificado

        Usuario = get_user_model()
        admin = Usuario.objects.create_superuser(
            username="super_diseno",
            password="admin1234",
            email="s@test.cl",
            rol=Rol.SUPERADMIN,
        )
        plantilla = DisenoCertificado.objects.create(junta=self.junta)
        self.client.force_login(admin)
        respuesta = self.client.get(reverse("admin:vecinos_disenocertificado_editor", args=[plantilla.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Personalizar certificado")
        self.client.post(
            reverse("admin:vecinos_disenocertificado_editor", args=[plantilla.pk]),
            {
                "titulo": "CERTIFICADO DE RESIDENCIA",
                "cuerpo": plantilla.cuerpo,
                "texto_verificacion": plantilla.texto_verificacion,
                "texto_pie": plantilla.texto_pie,
                "mostrar_logo": "on",
                "layout_json": '{"pagina": {"bg": "#F7F4EA"}, "encabezado": {"bg": "", "color": "#FFFFFF", "z": 1}, "titulo": {"x": 1.1, "y": 5, "w": 18, "h": 2, "font": 20, "align": "right", "fit": true, "color": "#123456", "z": 2}, "logo": {"x": 3.567, "y": 1.2, "w": 3, "h": 3, "font": 12, "zoom": 1.5, "panX": 0.2, "panY": -0.1, "z": 12}}',
            },
        )
        plantilla.refresh_from_db()
        self.assertEqual(plantilla.layout["titulo"]["x"], 1.1)
        self.assertEqual(plantilla.layout["logo"]["x"], 3.57)
        self.assertEqual(plantilla.layout["titulo"]["font"], 20)
        self.assertEqual(plantilla.layout["titulo"]["align"], "right")
        self.assertEqual(plantilla.layout["titulo"]["color"], "#123456")
        self.assertEqual(plantilla.layout["encabezado"]["bg"], "")
        self.assertEqual(plantilla.layout["pagina"]["bg"], "#F7F4EA")
        self.assertEqual(plantilla.layout["logo"]["zoom"], 1.5)
        self.assertEqual(plantilla.layout["logo"]["z"], 12)
        self.assertEqual(str(plantilla.logo_x), "3.57")
        from vecinos.layout import layout_completo, orden_pintado
        from vecinos.pdf import construir_pdf
        from vecinos.variables import certificado_muestra

        completo = layout_completo(plantilla)
        self.assertEqual(completo["encabezado"]["bg"], "")
        self.assertLess(completo["encabezado"]["z"], completo["logo"]["z"])
        self.assertEqual(orden_pintado(completo)[-1], "logo")
        pdf = construir_pdf(certificado_muestra(self.junta))
        self.assertTrue(pdf.startswith(b"%PDF"))
