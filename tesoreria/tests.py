from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import Rol
from juntas.models import Junta
from tesoreria.models import PagoCuota
from tesoreria.services import cuadro_anual, estado_cuotas
from vecinos.models import Vecino
from vecinos.services import emitir_certificado_web


class TesoreriaTests(TestCase):
    def setUp(self):
        self.junta = Junta.objects.create(
            nombre="Huente",
            slug="tesoreria-test",
            activa=True,
            valor_cuota=1000,
            certificado_con_deuda=False,
        )
        self.socio = Vecino.objects.create(
            junta=self.junta,
            rut="12345678-5",
            nombres="Juan",
            apellido_paterno="Pérez",
            direccion="Pasaje 1",
            fecha_ingreso=date(2026, 1, 10),
        )
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="dir_teso",
            password="huente1234",
            junta=self.junta,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )

    def test_deuda_desde_ingreso(self):
        estado = estado_cuotas(self.socio)
        self.assertTrue(estado["tiene_deuda"])
        self.assertGreaterEqual(estado["meses_deuda"], 1)
        self.assertEqual(estado["monto_deuda"], Decimal(1000) * estado["meses_deuda"])

    def test_certificado_bloqueado_con_deuda(self):
        cert, error = emitir_certificado_web(self.junta, "12.345.678-5", "127.0.0.1")
        self.assertIsNone(cert)
        self.assertIn("cuotas impagas", error)

    def test_pago_deja_al_dia_el_mes(self):
        hoy = date.today()
        PagoCuota.objects.create(vecino=self.socio, anio=hoy.year, mes=hoy.month, monto=1000)
        estado = estado_cuotas(self.socio)
        self.assertNotIn((hoy.year, hoy.month), estado["adeudados"])

    def test_directiva_ve_tesoreria(self):
        self.client.force_login(self.directiva)
        lista = self.client.get(reverse("admin:tesoreria_movimiento_changelist"))
        self.assertEqual(lista.status_code, 200)
        estado = self.client.get(reverse("admin:tesoreria_pagocuota_estado"))
        self.assertEqual(estado.status_code, 200)
        self.assertContains(estado, "Juan Pérez")
        self.assertContains(estado, "Solo morosos")
        self.assertContains(estado, "Ene")

    def test_cuadro_anual_muestra_hasta_donde_pago(self):
        PagoCuota.objects.create(vecino=self.socio, anio=2026, mes=1, monto=1000)
        PagoCuota.objects.create(vecino=self.socio, anio=2026, mes=2, monto=1000)
        PagoCuota.objects.create(vecino=self.socio, anio=2026, mes=3, monto=1000)
        PagoCuota.objects.create(vecino=self.socio, anio=2026, mes=4, monto=1000)
        PagoCuota.objects.create(vecino=self.socio, anio=2026, mes=5, monto=1000)
        cuadro = cuadro_anual(self.socio, 2026, date(2026, 10, 15))
        self.assertTrue(cuadro["es_moroso"])
        self.assertEqual(cuadro["ultimo_pagado"], 5)
        self.assertIn("mayo", cuadro["lectura"])
        self.assertIn("junio a octubre", cuadro["lectura"])
        self.assertEqual(cuadro["meses_deuda"], 5)

    def test_switch_morosos_oculta_al_dia(self):
        al_dia = Vecino.objects.create(
            junta=self.junta,
            rut="11111111-1",
            nombres="Ana",
            apellido_paterno="Soto",
            direccion="Calle 2",
            fecha_ingreso=date(2026, 10, 1),
        )
        PagoCuota.objects.create(vecino=al_dia, anio=2026, mes=10, monto=1000)
        self.client.force_login(self.directiva)
        todos = self.client.get(reverse("admin:tesoreria_pagocuota_estado"), {"anio": 2026})
        self.assertContains(todos, "Juan Pérez")
        self.assertContains(todos, "Ana Soto")
        morosos = self.client.get(reverse("admin:tesoreria_pagocuota_estado"), {"anio": 2026, "morosos": "1"})
        self.assertContains(morosos, "Juan Pérez")
        self.assertNotContains(morosos, "Ana Soto")
