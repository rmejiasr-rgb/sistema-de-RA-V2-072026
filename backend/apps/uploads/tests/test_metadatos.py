from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.models import AuditLog, Carga, Evaluacion, ResultadoEstudiante


class MetadatosTests(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Producción", codigo="PROD")
        self.materia = Materia.objects.create(codigo="M1", nombre="Materia 1", escuela=self.escuela)
        self.periodo = Periodo.objects.create(
            codigo="2526-3", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.ra = RACatalogo.objects.create(codigo="RA1", nombre="RA1")
        MateriaRA.objects.create(materia=self.materia, ra=self.ra, nivel_esperado=1)
        self.prof = Usuario.objects.create_user(username="prof", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.prof, rol=RolAsignado.PROFESOR, escuela=self.escuela)
        self.otro = Usuario.objects.create_user(username="otro", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.otro, rol=RolAsignado.PROFESOR, escuela=self.escuela)

        self.carga = Carga.objects.create(
            archivo="x.xlsx", archivo_nombre_original="x.xlsx", archivo_hash="a" * 64,
            version=1, estado=Carga.ESTADO_VALIDADA, usuario=self.prof,
            periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Richad Mejias", ra=self.ra, nivel=1,
        )
        self.ev = Evaluacion.objects.create(
            carga=self.carga, periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Richad Mejias", ra=self.ra, nivel=1, actividad="Actividad vieja",
            fecha_actividad=date(2026, 1, 1), pct_aprobados_declarado=Decimal("80"),
            pct_aprobados_recalculado=Decimal("80"), vigente=True,
        )
        self.estudiante = ResultadoEstudiante.objects.create(
            evaluacion=self.ev, grupo="1", nombre="Jose Perezz", carrera="Producción", nota=Decimal("80"),
        )
        self.client = APIClient()

    def test_editar_metadatos_registra_auditoria(self):
        self.client.force_authenticate(self.prof)
        resp = self.client.patch(
            f"/api/uploads/evaluaciones/{self.ev.id}/metadatos/",
            {"actividad": "Actividad corregida", "profesor_nombre": "Richard Mejías",
             "motivo": "Corrección de tipeo"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("actividad", resp.data["cambios"])
        self.assertIn("profesor_nombre", resp.data["cambios"])
        self.ev.refresh_from_db()
        self.assertEqual(self.ev.actividad, "Actividad corregida")
        self.carga.refresh_from_db()
        self.assertEqual(self.carga.profesor_nombre, "Richard Mejías")
        logs = AuditLog.objects.filter(entidad="Evaluacion", entidad_id=str(self.ev.id))
        self.assertEqual(logs.count(), 2)
        self.assertTrue(all(l.motivo == "Corrección de tipeo" for l in logs))

    def test_sin_cambios_no_registra(self):
        self.client.force_authenticate(self.prof)
        resp = self.client.patch(
            f"/api/uploads/evaluaciones/{self.ev.id}/metadatos/",
            {"actividad": "Actividad vieja", "motivo": "sin cambios"}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["cambios"], [])
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_otro_profesor_no_puede_editar(self):
        # Un profesor ni siquiera ve la carga de otro (§3) → 404, no 403.
        self.client.force_authenticate(self.otro)
        resp = self.client.patch(
            f"/api/uploads/evaluaciones/{self.ev.id}/metadatos/",
            {"actividad": "Hackeada", "motivo": "x"}, format="json",
        )
        self.assertEqual(resp.status_code, 404)
        self.ev.refresh_from_db()
        self.assertEqual(self.ev.actividad, "Actividad vieja")

    def test_editar_nombre_estudiante(self):
        self.client.force_authenticate(self.prof)
        resp = self.client.patch(
            f"/api/uploads/estudiantes/{self.estudiante.id}/metadatos/",
            {"nombre": "José Pérez", "motivo": "Corrección de nombre"}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.estudiante.refresh_from_db()
        self.assertEqual(self.estudiante.nombre, "José Pérez")
        self.assertTrue(AuditLog.objects.filter(entidad="ResultadoEstudiante").exists())

    def test_coordinador_puede_editar_carga_de_otro(self):
        coord = Usuario.objects.create_user(username="coord", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=coord, rol=RolAsignado.COORDINADOR, escuela=self.escuela)
        self.client.force_authenticate(coord)
        resp = self.client.patch(
            f"/api/uploads/evaluaciones/{self.ev.id}/metadatos/",
            {"actividad": "Editada por coordinador", "motivo": "revisión"}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
