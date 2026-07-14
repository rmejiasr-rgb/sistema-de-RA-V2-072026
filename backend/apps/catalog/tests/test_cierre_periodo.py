from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.models import Carga, Evaluacion


class CierrePeriodoTests(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Producción", codigo="PROD")
        self.materia = Materia.objects.create(codigo="M1", nombre="Materia 1", escuela=self.escuela)
        self.periodo = Periodo.objects.create(
            codigo="2526-3", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.ra1 = RACatalogo.objects.create(codigo="RA1", nombre="RA1")
        self.ra2 = RACatalogo.objects.create(codigo="RA2", nombre="RA2")
        MateriaRA.objects.create(materia=self.materia, ra=self.ra1, nivel_esperado=1)
        MateriaRA.objects.create(materia=self.materia, ra=self.ra2, nivel_esperado=1)

        self.profesor = Usuario.objects.create_user(username="prof", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.profesor, rol=RolAsignado.PROFESOR, escuela=self.escuela)
        self.coordinador = Usuario.objects.create_user(username="coord", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.coordinador, rol=RolAsignado.COORDINADOR, escuela=self.escuela)

        self.client = APIClient()

    def _carga_eval(self, ra):
        carga = Carga.objects.create(
            archivo="x.xlsx", archivo_nombre_original="x.xlsx",
            archivo_hash=(str(ra.id) * 64)[:64], version=1,
            estado=Carga.ESTADO_VALIDADA, usuario=self.profesor,
            periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Prof", ra=ra, nivel=1,
        )
        Evaluacion.objects.create(
            carga=carga, periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Prof", ra=ra, nivel=1, actividad="A",
            fecha_actividad=date(2026, 1, 1), pct_aprobados_declarado=Decimal("80"),
            pct_aprobados_recalculado=Decimal("80"), vigente=True,
        )

    def test_no_cierra_con_incompletos(self):
        self._carga_eval(self.ra1)  # falta RA2
        self.client.force_authenticate(self.coordinador)
        resp = self.client.post(f"/api/catalog/periodos/{self.periodo.id}/cerrar/")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["n_incompletas"], 1)
        self.assertIn("RA2", resp.data["incompletas"][0]["faltantes"])
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.estado, Periodo.ESTADO_ABIERTO)

    def test_cierra_cuando_completo(self):
        self._carga_eval(self.ra1)
        self._carga_eval(self.ra2)
        self.client.force_authenticate(self.coordinador)
        resp = self.client.post(f"/api/catalog/periodos/{self.periodo.id}/cerrar/")
        self.assertEqual(resp.status_code, 200)
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.estado, Periodo.ESTADO_CERRADO)

    def test_profesor_no_puede_cerrar(self):
        self._carga_eval(self.ra1)
        self._carga_eval(self.ra2)
        self.client.force_authenticate(self.profesor)
        resp = self.client.post(f"/api/catalog/periodos/{self.periodo.id}/cerrar/")
        self.assertEqual(resp.status_code, 403)

    def test_completitud_preview(self):
        self._carga_eval(self.ra1)
        self.client.force_authenticate(self.coordinador)
        resp = self.client.get(f"/api/catalog/periodos/{self.periodo.id}/completitud/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["puede_cerrarse"])
        self.assertEqual(resp.data["n_incompletas"], 1)
