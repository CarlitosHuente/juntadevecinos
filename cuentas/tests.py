from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import NOMBRE_GRUPO, Rol, asegurar_grupos
from juntas.models import Junta


class RolesAdminTests(TestCase):
    def setUp(self):
        asegurar_grupos()
        self.junta = Junta.objects.create(nombre="Huente", slug="roles-admin", activa=True)
        Usuario = get_user_model()
        self.directiva = Usuario.objects.create_user(
            username="dir_roles",
            password="huente1234",
            junta=self.junta,
            rol=Rol.DIRECTIVA,
            is_staff=True,
        )
        self.comunicador = Usuario.objects.create_user(
            username="com_roles",
            password="huente1234",
            junta=self.junta,
            rol=Rol.COMUNICADOR,
            is_staff=True,
        )

    def test_usuario_queda_en_el_grupo_del_rol(self):
        self.assertTrue(self.directiva.groups.filter(name="Directiva").exists())
        self.assertTrue(self.comunicador.groups.filter(name="Comunicador").exists())

    def test_directiva_crea_grupo_y_asigna_acciones(self):
        self.client.force_login(self.directiva)
        lista = self.client.get(reverse("admin:auth_group_changelist"))
        self.assertEqual(lista.status_code, 200)
        self.assertContains(lista, "Directiva")
        alta = self.client.get(reverse("admin:auth_group_add"))
        self.assertEqual(alta.status_code, 200)
        self.assertContains(alta, "Acciones")
        tesoreria = Permission.objects.filter(content_type__app_label="tesoreria")
        self.assertTrue(tesoreria.exists())
        crear = self.client.post(
            reverse("admin:auth_group_add"),
            {
                "name": "Tesorero",
                "permissions": list(tesoreria.values_list("pk", flat=True)),
                "usuarios": [self.comunicador.pk],
            },
        )
        self.assertEqual(crear.status_code, 302)
        grupo = Group.objects.get(name="Tesorero")
        self.assertTrue(grupo.permissions.filter(content_type__app_label="tesoreria").exists())
        self.assertTrue(self.comunicador.groups.filter(name="Tesorero").exists())
        self.client.force_login(self.comunicador)
        self.assertEqual(self.client.get(reverse("admin:tesoreria_pagocuota_changelist")).status_code, 200)

    def test_no_borra_directiva_ni_superadmin(self):
        self.client.force_login(self.directiva)
        grupo = Group.objects.get(name="Directiva")
        self.assertEqual(self.client.post(reverse("admin:auth_group_delete", args=[grupo.pk])).status_code, 403)

    def test_directiva_no_asigna_superadmin(self):
        self.client.force_login(self.directiva)
        alta = self.client.get(reverse("admin:cuentas_usuario_add"))
        self.assertEqual(alta.status_code, 200)
        self.assertContains(alta, "groups")
        self.assertNotContains(alta, f">{NOMBRE_GRUPO[Rol.SUPERADMIN]}<")
