from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Escuela, Materia, MateriaRA, RACatalogo


class GestionCatalogoTests(TestCase):
    def setUp(self):
        self.esc_a = Escuela.objects.create(nombre="Escuela A", codigo="A")
        self.esc_b = Escuela.objects.create(nombre="Escuela B", codigo="B")
        self.mat_a = Materia.objects.create(codigo="MA", nombre="Mat A", escuela=self.esc_a)
        self.mat_b = Materia.objects.create(codigo="MB", nombre="Mat B", escuela=self.esc_b)
        self.ra = RACatalogo.objects.create(codigo="RA1", nombre="RA1")

        self.coord_a = Usuario.objects.create_user(username="coordA", password="x", escuela=self.esc_a)
        RolAsignado.objects.create(usuario=self.coord_a, rol=RolAsignado.COORDINADOR, escuela=self.esc_a)
        self.profesor = Usuario.objects.create_user(username="prof", password="x", escuela=self.esc_a)
        RolAsignado.objects.create(usuario=self.profesor, rol=RolAsignado.PROFESOR, escuela=self.esc_a)
        self.client = APIClient()

    def test_coordinador_crea_en_su_escuela(self):
        self.client.force_authenticate(self.coord_a)
        resp = self.client.post("/api/catalog/materia-ras/",
                                {"materia": self.mat_a.id, "ra": self.ra.id, "nivel_esperado": 2}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(MateriaRA.objects.filter(materia=self.mat_a, ra=self.ra).exists())

    def test_coordinador_no_puede_en_otra_escuela(self):
        self.client.force_authenticate(self.coord_a)
        resp = self.client.post("/api/catalog/materia-ras/",
                                {"materia": self.mat_b.id, "ra": self.ra.id, "nivel_esperado": 2}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_profesor_no_puede_gestionar(self):
        self.client.force_authenticate(self.profesor)
        resp = self.client.post("/api/catalog/materia-ras/",
                                {"materia": self.mat_a.id, "ra": self.ra.id, "nivel_esperado": 2}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_lectura_permitida_a_todos(self):
        self.client.force_authenticate(self.profesor)
        resp = self.client.get("/api/catalog/materia-ras/")
        self.assertEqual(resp.status_code, 200)


class GestionUsuariosTests(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Escuela A", codigo="A")
        self.admin = Usuario.objects.create_superuser(username="admin", password="x", email="a@a.com")
        self.coord = Usuario.objects.create_user(username="coord", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.coord, rol=RolAsignado.COORDINADOR, escuela=self.escuela)
        self.client = APIClient()

    def test_admin_crea_usuario_con_roles(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/auth/usuarios/", {
            "username": "nuevo", "email": "n@u.com", "first_name": "Nuevo", "last_name": "User",
            "escuela": self.escuela.id, "password": "clave12345",
            "roles_input": [{"rol": "PROFESOR", "escuela": self.escuela.id}],
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        nuevo = Usuario.objects.get(username="nuevo")
        self.assertTrue(nuevo.check_password("clave12345"))
        self.assertTrue(nuevo.tiene_rol("PROFESOR"))

    def test_coordinador_no_puede_gestionar_usuarios(self):
        self.client.force_authenticate(self.coord)
        resp = self.client.get("/api/auth/usuarios/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_edita_roles(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(f"/api/auth/usuarios/{self.coord.id}/", {
            "roles_input": [{"rol": "COORDINADOR", "escuela": self.escuela.id},
                            {"rol": "PROFESOR", "escuela": self.escuela.id}],
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.coord.refresh_from_db()
        self.assertTrue(self.coord.tiene_rol("PROFESOR"))
        self.assertTrue(self.coord.tiene_rol("COORDINADOR"))
