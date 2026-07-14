from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.models import (
    AuditLog,
    Carga,
    Criterio,
    Evaluacion,
    ResultadoCriterio,
    ResultadoEstudiante,
)


class ExportTests(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Producción", codigo="PROD")
        self.materia = Materia.objects.create(codigo="M1", nombre="Materia 1", escuela=self.escuela)
        self.periodo = Periodo.objects.create(
            codigo="2526-3", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.ra = RACatalogo.objects.create(codigo="RA1", nombre="RA1")
        MateriaRA.objects.create(materia=self.materia, ra=self.ra, nivel_esperado=1)
        self.admin = Usuario.objects.create_superuser(username="admin", password="x", email="a@a.com")

        carga = Carga.objects.create(
            archivo="x.xlsx", archivo_nombre_original="x.xlsx", archivo_hash="a" * 64,
            version=1, estado=Carga.ESTADO_VALIDADA, usuario=self.admin,
            periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Prof", ra=self.ra, nivel=1,
        )
        ev = Evaluacion.objects.create(
            carga=carga, periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Prof", ra=self.ra, nivel=1, actividad="A",
            fecha_actividad=date(2026, 1, 1), pct_aprobados_declarado=Decimal("80"),
            pct_aprobados_recalculado=Decimal("80"), vigente=True,
        )
        crit = Criterio.objects.create(evaluacion=ev, nombre="Criterio 1", orden=1)
        est = ResultadoEstudiante.objects.create(
            evaluacion=ev, grupo="1", nombre="Estudiante A", carrera="Producción", nota=Decimal("80")
        )
        ResultadoCriterio.objects.create(
            resultado_estudiante=est, criterio=crit, nivel=ResultadoCriterio.SATISFACTORIO
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_export_excel(self):
        resp = self.client.get("/api/dashboard/export/excel/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spreadsheetml", resp["Content-Type"])
        self.assertTrue(resp["Content-Disposition"].endswith('.xlsx"'))
        self.assertTrue(len(resp.content) > 0)
        self.assertTrue(AuditLog.objects.filter(entidad="Exportacion", entidad_id="EXCEL").exists())

    def test_export_pdf(self):
        resp = self.client.get(f"/api/dashboard/export/pdf/?periodo={self.periodo.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))
        self.assertTrue(AuditLog.objects.filter(entidad="Exportacion", entidad_id="PDF").exists())
