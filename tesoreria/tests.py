from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import Rol
from juntas.models import Junta
from tesoreria.models import PagoCuota
from tesoreria.services import estado_cuotas
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
