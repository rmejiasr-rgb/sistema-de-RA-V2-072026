import os
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.models import Evaluacion
from apps.uploads.services import CargaRechazada, procesar_carga

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
RA10_PATH = os.path.join(FIXTURES, "FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx")


def _archivo_ra10():
    with open(RA10_PATH, "rb") as f:
        contenido = f.read()
    return SimpleUploadedFile(
        "FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx",
        contenido,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@override_settings(MEDIA_ROOT="/tmp/sistema_ra_test_media")
class ProcesarCargaEndToEndTests(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Producción", codigo="PROD")
        self.materia = Materia.objects.create(codigo="FPTPI13", nombre="Productividad", escuela=self.escuela)
        self.periodo = Periodo.objects.create(
            codigo="2526-3", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.ra10 = RACatalogo.objects.create(codigo="RA10-IP", nombre="RA10 IP")
        MateriaRA.objects.create(materia=self.materia, ra=self.ra10, nivel_esperado=3)
        self.usuario = Usuario.objects.create_user(username="rmejias", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.usuario, rol=RolAsignado.PROFESOR, escuela=self.escuela)
        self.otro_usuario = Usuario.objects.create_user(username="otro", password="x", escuela=self.escuela)

    def test_carga_valida_persiste_evaluacion_y_recalculo_coincide(self):
        carga, reporte = procesar_carga(_archivo_ra10(), self.usuario)
        self.assertTrue(reporte["aceptado"])
        evaluacion = Evaluacion.objects.get(carga=carga)
        self.assertEqual(evaluacion.pct_aprobados_declarado, Decimal("90.000"))
        self.assertEqual(evaluacion.pct_aprobados_recalculado, Decimal("90.000"))
        self.assertTrue(evaluacion.vigente)
        self.assertEqual(evaluacion.resultados_estudiantes.count(), 45)
        self.assertEqual(evaluacion.criterios.count(), 4)

    def test_resubida_misma_clave_sin_confirmar_no_crea_version(self):
        procesar_carga(_archivo_ra10(), self.usuario)
        with self.assertRaises(CargaRechazada) as ctx:
            procesar_carga(_archivo_ra10(), self.usuario, confirmar_nueva_version=False)
        self.assertTrue(ctx.exception.resultado_json["requiere_confirmacion"])
        self.assertEqual(Evaluacion.objects.filter(vigente=True).count(), 1)

    def test_resubida_confirmada_crea_nueva_version_y_conserva_anterior(self):
        carga_v1, _ = procesar_carga(_archivo_ra10(), self.usuario)
        carga_v2, reporte = procesar_carga(_archivo_ra10(), self.usuario, confirmar_nueva_version=True)

        self.assertEqual(carga_v2.version, 2)
        self.assertTrue(reporte["aceptado"])

        eval_v1 = Evaluacion.objects.get(carga=carga_v1)
        eval_v2 = Evaluacion.objects.get(carga=carga_v2)
        eval_v1.refresh_from_db()

        self.assertFalse(eval_v1.vigente)
        self.assertTrue(eval_v2.vigente)
        # La versión anterior sigue consultable
        self.assertEqual(Evaluacion.objects.filter(carga__materia=self.materia).count(), 2)
        self.assertEqual(Evaluacion.objects.filter(vigente=True).count(), 1)

    def test_otro_usuario_no_puede_resubir_clave_de_otro(self):
        procesar_carga(_archivo_ra10(), self.usuario)
        with self.assertRaises(CargaRechazada) as ctx:
            procesar_carga(_archivo_ra10(), self.otro_usuario)
        errores = ctx.exception.resultado_json["errores"]
        self.assertEqual(errores[0]["codigo"], "V4_DUPLICADO_OTRO_USUARIO")
