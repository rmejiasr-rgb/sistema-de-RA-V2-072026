from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import RolAsignado, Usuario
from apps.catalog.models import Carrera, Escuela, Materia, MateriaRA, Periodo, RACatalogo
from apps.uploads.parser import ArchivoParseado, EstudianteParseado
from apps.uploads.validators import materia_seccion_completa, validar_carga


def construir_datos(**overrides):
    base = dict(
        asignatura_texto="PRODUCTIVIDAD Y MEDICIÓN DEL TRABAJO",
        seccion="1",
        profesor="Richard José Mejías",
        periodo_codigo="2526-3",
        actividad="Actividad de prueba",
        fecha_actividad=date(2026, 7, 8),
        ra_codigo="RA10-IP",
        nivel=3,
        pct_aprobados_declarado=Decimal("50.000"),
        criterios=["Criterio 1"],
        estudiantes=[
            EstudianteParseado(35, "1", "Estudiante Uno", "Producción", Decimal("50"), {"Criterio 1": "Satisfactorio"}),
            EstudianteParseado(36, "1", "Estudiante Dos", "Producción", Decimal("50"), {"Criterio 1": "Insatisfactorio"}),
        ],
        nombre_archivo_info={
            "codmat": "FPTPI13", "seccion": "1", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 3,
        },
    )
    base.update(overrides)
    return ArchivoParseado(**base)


class ValidadorTestBase(TestCase):
    def setUp(self):
        self.escuela = Escuela.objects.create(nombre="Producción", codigo="PROD")
        self.materia = Materia.objects.create(codigo="FPTPI13", nombre="Productividad", escuela=self.escuela)
        self.periodo = Periodo.objects.create(
            codigo="2526-3", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.ra10 = RACatalogo.objects.create(codigo="RA10-IP", nombre="RA10 IP")
        self.ra11 = RACatalogo.objects.create(codigo="RA11-IP", nombre="RA11 IP")
        MateriaRA.objects.create(materia=self.materia, ra=self.ra10, nivel_esperado=3)
        MateriaRA.objects.create(materia=self.materia, ra=self.ra11, nivel_esperado=3)
        self.usuario = Usuario.objects.create_user(username="rmejias", password="x", escuela=self.escuela)
        RolAsignado.objects.create(usuario=self.usuario, rol=RolAsignado.PROFESOR, escuela=self.escuela)
        self.otro_usuario = Usuario.objects.create_user(username="otro", password="x", escuela=self.escuela)


class V2ConsistenciaTests(ValidadorTestBase):
    def test_pasa_cuando_coincide(self):
        r = validar_carga(construir_datos(), "archivo.xlsx", self.usuario)
        self.assertTrue(r.aceptado)

    def test_rechaza_discrepancia_seccion(self):
        datos = construir_datos(nombre_archivo_info={
            "codmat": "FPTPI13", "seccion": "2", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 3,
        })
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V2_DISCREPANCIA")

    def test_rechaza_nombre_archivo_no_reconocido(self):
        datos = construir_datos(nombre_archivo_info=None)
        r = validar_carga(datos, "cualquiera.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V2_NOMBRE_ARCHIVO")


class V3CatalogoTests(ValidadorTestBase):
    def test_rechaza_materia_no_catalogada(self):
        datos = construir_datos(nombre_archivo_info={
            "codmat": "NOEXISTE", "seccion": "1", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 3,
        })
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V3_MATERIA_NO_CATALOGADA")

    def test_rechaza_ra_no_esperado_para_materia(self):
        otra_materia = Materia.objects.create(codigo="FPTPI99", nombre="Otra", escuela=self.escuela)
        ra_suelto = RACatalogo.objects.create(codigo="RA99", nombre="RA99")
        MateriaRA.objects.create(materia=otra_materia, ra=ra_suelto, nivel_esperado=1)
        datos = construir_datos(nombre_archivo_info={
            "codmat": "FPTPI99", "seccion": "1", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 3,
        })
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V3_RA_NO_ESPERADO")

    def test_rechaza_nivel_no_esperado(self):
        datos = construir_datos(nivel=1, nombre_archivo_info={
            "codmat": "FPTPI13", "seccion": "1", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 1,
        })
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V3_NIVEL_NO_ESPERADO")


class V4DuplicadoVersionTests(ValidadorTestBase):
    def _crear_evaluacion_vigente(self, usuario, seccion="1", ra=None):
        from apps.uploads.models import Carga, Evaluacion

        carga = Carga.objects.create(
            archivo="cargas/x.xlsx", archivo_nombre_original="x.xlsx", archivo_hash="a" * 64,
            version=1, estado=Carga.ESTADO_VALIDADA, usuario=usuario,
            periodo=self.periodo, materia=self.materia, seccion=seccion,
            profesor_nombre="Richard José Mejías", ra=ra or self.ra10, nivel=3,
        )
        return Evaluacion.objects.create(
            carga=carga, periodo=self.periodo, materia=self.materia, seccion=seccion,
            profesor_nombre="Richard José Mejías", ra=ra or self.ra10, nivel=3,
            actividad="Actividad previa", fecha_actividad=date(2026, 1, 1),
            pct_aprobados_declarado=Decimal("50"), pct_aprobados_recalculado=Decimal("50"),
            vigente=True,
        )

    def test_mismo_usuario_requiere_confirmacion_y_no_duplica(self):
        self._crear_evaluacion_vigente(self.usuario)
        r = validar_carga(construir_datos(), "archivo.xlsx", self.usuario, confirmar_nueva_version=False)
        self.assertTrue(r.aceptado)
        self.assertTrue(r.requiere_confirmacion)

    def test_mismo_usuario_confirmando_acepta(self):
        self._crear_evaluacion_vigente(self.usuario)
        r = validar_carga(construir_datos(), "archivo.xlsx", self.usuario, confirmar_nueva_version=True)
        self.assertTrue(r.aceptado)
        self.assertFalse(r.requiere_confirmacion)
        self.assertIsNotNone(r.evaluacion_anterior)

    def test_otro_usuario_no_coordinador_rechaza(self):
        self._crear_evaluacion_vigente(self.usuario)
        r = validar_carga(construir_datos(), "archivo.xlsx", self.otro_usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V4_DUPLICADO_OTRO_USUARIO")

    def test_seccion_2_misma_materia_profesor_es_permitida(self):
        self._crear_evaluacion_vigente(self.usuario, seccion="1")
        datos_seccion_2 = construir_datos(seccion="2", nombre_archivo_info={
            "codmat": "FPTPI13", "seccion": "2", "profesor": "RICHARD MEJIAS",
            "periodo": "2526-3", "ra": "RA10-IP", "nivel": 3,
        })
        r = validar_carga(datos_seccion_2, "archivo.xlsx", self.usuario)
        self.assertTrue(r.aceptado)
        self.assertFalse(r.requiere_confirmacion)


class V5DatosTests(ValidadorTestBase):
    def test_rechaza_nivel_criterio_invalido(self):
        datos = construir_datos(estudiantes=[
            EstudianteParseado(35, "1", "Estudiante Uno", "Producción", Decimal("50"), {"Criterio 1": "Regular"}),
        ])
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V5_NIVEL_INVALIDO")

    def test_rechaza_nota_fuera_de_rango(self):
        datos = construir_datos(estudiantes=[
            EstudianteParseado(35, "1", "Estudiante Uno", "Producción", Decimal("150"), {"Criterio 1": "Satisfactorio"}),
        ])
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V5_NOTA_FUERA_DE_RANGO")

    def test_rechaza_estudiante_duplicado(self):
        datos = construir_datos(estudiantes=[
            EstudianteParseado(35, "1", "Estudiante Uno", "Producción", Decimal("50"), {"Criterio 1": "Satisfactorio"}),
            EstudianteParseado(36, "1", "Estudiante Uno", "Producción", Decimal("60"), {"Criterio 1": "Satisfactorio"}),
        ])
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertFalse(r.aceptado)
        self.assertEqual(r.errores[0].codigo, "V5_ESTUDIANTE_DUPLICADO")

    def test_discrepancia_pct_es_advertencia_no_rechazo(self):
        datos = construir_datos(pct_aprobados_declarado=Decimal("99.000"))
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertTrue(r.aceptado)
        self.assertEqual(r.advertencias[0].codigo, "V5_DISCREPANCIA_PCT")
        self.assertEqual(r.pct_aprobados_recalculado, Decimal("50.000"))

    def test_pct_recalculado_coincide_cuando_declarado_correcto(self):
        datos = construir_datos(pct_aprobados_declarado=Decimal("50.000"))
        r = validar_carga(datos, "archivo.xlsx", self.usuario)
        self.assertTrue(r.aceptado)
        self.assertFalse(any(a.codigo == "V5_DISCREPANCIA_PCT" for a in r.advertencias))


class V6CompletitudTests(ValidadorTestBase):
    def test_incompleta_si_falta_un_ra(self):
        from apps.uploads.models import Carga, Evaluacion

        carga = Carga.objects.create(
            archivo="cargas/x.xlsx", archivo_nombre_original="x.xlsx", archivo_hash="b" * 64,
            version=1, estado=Carga.ESTADO_VALIDADA, usuario=self.usuario,
            periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Richard José Mejías", ra=self.ra10, nivel=3,
        )
        Evaluacion.objects.create(
            carga=carga, periodo=self.periodo, materia=self.materia, seccion="1",
            profesor_nombre="Richard José Mejías", ra=self.ra10, nivel=3,
            actividad="A", fecha_actividad=date(2026, 1, 1),
            pct_aprobados_declarado=Decimal("50"), pct_aprobados_recalculado=Decimal("50"), vigente=True,
        )
        completa, esperados, faltantes = materia_seccion_completa(
            self.periodo, self.materia, "1", "Richard José Mejías"
        )
        self.assertFalse(completa)
        self.assertEqual(len(faltantes), 1)

    def test_completa_cuando_todos_los_ras_cargados(self):
        from apps.uploads.models import Carga, Evaluacion

        for ra in (self.ra10, self.ra11):
            carga = Carga.objects.create(
                archivo="cargas/x.xlsx", archivo_nombre_original="x.xlsx", archivo_hash=(str(ra.id) * 64)[:64],
                version=1, estado=Carga.ESTADO_VALIDADA, usuario=self.usuario,
                periodo=self.periodo, materia=self.materia, seccion="1",
                profesor_nombre="Richard José Mejías", ra=ra, nivel=3,
            )
            Evaluacion.objects.create(
                carga=carga, periodo=self.periodo, materia=self.materia, seccion="1",
                profesor_nombre="Richard José Mejías", ra=ra, nivel=3,
                actividad="A", fecha_actividad=date(2026, 1, 1),
                pct_aprobados_declarado=Decimal("50"), pct_aprobados_recalculado=Decimal("50"), vigente=True,
            )
        completa, esperados, faltantes = materia_seccion_completa(
            self.periodo, self.materia, "1", "Richard José Mejías"
        )
        self.assertTrue(completa)
        self.assertEqual(len(faltantes), 0)
