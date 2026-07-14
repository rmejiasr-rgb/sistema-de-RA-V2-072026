import os
from decimal import Decimal

from django.test import SimpleTestCase

from apps.uploads.parser import ParserError, parse_workbook, parsear_nombre_archivo

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
RA10_PATH = os.path.join(FIXTURES, "FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx")
RA11_PATH = os.path.join(FIXTURES, "FPTPI13-1-RICHARD_MEJIAS-2526-3-RA11-IP-N3.xlsx")


class ParseNombreArchivoTests(SimpleTestCase):
    def test_nombre_valido(self):
        info = parsear_nombre_archivo("FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx")
        self.assertEqual(info["codmat"], "FPTPI13")
        self.assertEqual(info["seccion"], "1")
        self.assertEqual(info["profesor"], "RICHARD MEJIAS")
        self.assertEqual(info["periodo"], "2526-3")
        self.assertEqual(info["ra"], "RA10-IP")
        self.assertEqual(info["nivel"], 3)

    def test_nombre_sin_patron(self):
        self.assertIsNone(parsear_nombre_archivo("archivo_cualquiera.xlsx"))


class ParseWorkbookRA10Tests(SimpleTestCase):
    """Valores exactos contra el archivo real RA10 IP N3."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(RA10_PATH, "rb") as f:
            cls.datos = parse_workbook(f, os.path.basename(RA10_PATH))

    def test_cabecera(self):
        d = self.datos
        self.assertEqual(d.asignatura_texto, "PRODUCTIVIDAD Y MEDICIÓN DEL TRABAJO")
        self.assertEqual(d.seccion, "1")
        self.assertEqual(d.profesor, "Richard José Mejías")
        self.assertEqual(d.periodo_codigo, "2526-3")
        self.assertEqual(d.ra_codigo, "RA10-IP")
        self.assertEqual(d.nivel, 3)
        self.assertEqual(d.pct_aprobados_declarado, Decimal("90.000"))

    def test_numero_criterios(self):
        self.assertEqual(len(self.datos.criterios), 4)
        self.assertIn("Identificación y análisis de problemas de ingeniería", self.datos.criterios)

    def test_numero_estudiantes(self):
        self.assertEqual(len(self.datos.estudiantes), 45)

    def test_notas_estudiantes_conocidas(self):
        por_nombre = {e.nombre: e.nota for e in self.datos.estudiantes}
        self.assertEqual(por_nombre["Alana Laweiko"], Decimal("50.000"))
        self.assertEqual(por_nombre["Ariannis Karacachian"], Decimal("75.000"))
        self.assertEqual(por_nombre["Diego Bejarano"], Decimal("12.500"))

    def test_niveles_criterio_estudiante(self):
        est = next(e for e in self.datos.estudiantes if e.nombre == "Ariannis Karacachian")
        self.assertEqual(
            est.niveles_por_criterio["Identificación y análisis de problemas de ingeniería"],
            "Excelente",
        )


class ParseWorkbookRA11Tests(SimpleTestCase):
    """Valores exactos contra el archivo real RA11 IP N3 (con encabezado 'Criterios'
    en lugar de 'Nombre y Apellido': ejercita el fallback de detección de fila)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(RA11_PATH, "rb") as f:
            cls.datos = parse_workbook(f, os.path.basename(RA11_PATH))

    def test_cabecera(self):
        d = self.datos
        self.assertEqual(d.ra_codigo, "RA11-IP")
        self.assertEqual(d.nivel, 3)
        self.assertEqual(d.pct_aprobados_declarado, Decimal("86.667"))

    def test_numero_criterios(self):
        self.assertEqual(len(self.datos.criterios), 3)

    def test_numero_estudiantes(self):
        self.assertEqual(len(self.datos.estudiantes), 45)

    def test_notas_estudiantes_conocidas(self):
        por_nombre = {e.nombre: e.nota for e in self.datos.estudiantes}
        self.assertEqual(por_nombre["Ariannis Karacachian"], Decimal("100.000"))
        self.assertEqual(por_nombre["Diego Bejarano"], Decimal("0.000"))


class ParseWorkbookEstructuraInvalidaTests(SimpleTestCase):
    def test_archivo_no_excel(self):
        import io

        with self.assertRaises(ParserError):
            parse_workbook(io.BytesIO(b"esto no es un xlsx"), "cualquiera.xlsx")
