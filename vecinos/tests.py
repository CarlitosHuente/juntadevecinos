from django.test import TestCase

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
